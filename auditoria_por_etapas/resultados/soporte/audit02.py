"""Herramienta reproducible de preparación, arranque, prueba e inspección para la Etapa 02."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path


SOPORTE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = SOPORTE_DIR.parent
ETAPAS_DIR = RESULTADOS_DIR.parent
REPO_ROOT = ETAPAS_DIR.parent
APP_ROOT = REPO_ROOT / "r1-pmv"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(SOPORTE_DIR) not in sys.path:
    sys.path.insert(0, str(SOPORTE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "audit02_settings")

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.management import call_command, execute_from_command_line  # noqa: E402
from django.utils import timezone  # noqa: E402


AUDIT_USERS = [
    {
        "email": "admin@minimarket.local",
        "display_name": "Ana Administradora",
        "role_code": "ADMIN",
        "is_active": True,
        "password": "Audit02!Adm",
    },
    {
        "email": "almacen@minimarket.local",
        "display_name": "Bruno Almacenero",
        "role_code": "ALMACENERO",
        "is_active": True,
        "password": "Audit02!Alm",
    },
    {
        "email": "ventas@minimarket.local",
        "display_name": "Carla Vendedora",
        "role_code": "VENDEDOR",
        "is_active": True,
        "password": "Audit02!Ven",
    },
    {
        "email": "ventas2@minimarket.local",
        "display_name": "Diego Vendedor",
        "role_code": "VENDEDOR",
        "is_active": True,
        "password": "Audit02!Ve2",
    },
    {
        "email": "inactivo@minimarket.local",
        "display_name": "Elena Inactiva",
        "role_code": "VENDEDOR",
        "is_active": False,
        "password": "Audit02!Ina",
    },
]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_safe_db() -> Path:
    db_path = Path(settings.DATABASES["default"]["NAME"]).resolve()
    protected = {
        (APP_ROOT / "r1_pmv.sqlite3").resolve(),
        (RESULTADOS_DIR / "datos" / "etapa00-20261105" / "audit.sqlite3").resolve(),
        (RESULTADOS_DIR / "datos" / "etapa01-20261109" / "audit.sqlite3").resolve(),
    }
    if db_path in protected:
        raise RuntimeError(f"Operación abortada: intento de usar base protegida {db_path}")
    return db_path


def cmd_prepare(args: argparse.Namespace) -> int:
    django.setup()
    db_path = ensure_safe_db()
    need_flush = False
    if args.reset and db_path.exists():
        try:
            db_path.unlink()
            for suffix in ("-wal", "-shm", "-journal"):
                aux = Path(f"{db_path}{suffix}")
                if aux.exists():
                    aux.unlink()
        except PermissionError:
            need_flush = True

    call_command("migrate", verbosity=0, interactive=False)
    if need_flush:
        call_command("flush", verbosity=0, interactive=False)

    from cash.models import CashRegister
    from catalog.models import Category, Product
    from identity.models import Account, LoginAttempt, Role
    from inventory.models import InitialInventoryLoad, Lot

    role_labels = {
        Role.Code.ADMIN: "Administrador",
        Role.Code.WAREHOUSE: "Almacenero",
        Role.Code.SELLER: "Vendedor",
    }
    roles: dict[str, Role] = {}
    for code, name in role_labels.items():
        role, _ = Role.objects.update_or_create(code=code, defaults={"name": name})
        roles[code] = role

    created_accounts: dict[str, Account] = {}
    for spec in AUDIT_USERS:
        normalized = Account.normalize_email(spec["email"])
        account = Account.objects.filter(email_normalized=normalized).first()
        if account is None:
            account = Account(
                email=spec["email"],
                email_normalized=normalized,
                display_name=spec["display_name"],
                role=roles[spec["role_code"]],
                is_active=spec["is_active"],
                is_staff=False,
            )
        else:
            account.email = spec["email"]
            account.email_normalized = normalized
            account.display_name = spec["display_name"]
            account.role = roles[spec["role_code"]]
            account.is_active = spec["is_active"]
            account.is_staff = False
        account.set_password(spec["password"])
        account.full_clean()
        account.save()
        created_accounts[spec["email"]] = account

    LoginAttempt.objects.all().delete()

    register, _ = CashRegister.objects.get_or_create(code="CAJA-01")
    category, _ = Category.objects.get_or_create(name="Productos enlatados")
    product, _ = Product.objects.update_or_create(
        barcode="775000000201",
        defaults={
            "category": category,
            "name": "Atún Audit02 en lata",
            "sale_price": Decimal("8.50"),
            "is_active": True,
        },
    )
    warehouse_user = created_accounts["almacen@minimarket.local"]
    load, _ = InitialInventoryLoad.objects.get_or_create(
        product=product,
        defaults={"responsible": warehouse_user},
    )
    lot, _ = Lot.objects.update_or_create(
        product=product,
        number="LOT-AUD02-01",
        defaults={
            "initial_load": load,
            "initial_quantity": 20,
            "available_quantity": 20,
            "unit_cost": Decimal("5.0000"),
            "expiration_date": timezone.localdate() + timedelta(days=30),
        },
    )

    manifest = {
        "stage": "ETAPA-02",
        "prepared_at": datetime.now().isoformat(),
        "database_path": str(db_path.relative_to(REPO_ROOT).as_posix()),
        "database_sha256": sha256_file(db_path),
        "protected_databases": {
            "r1_pmv.sqlite3": sha256_file(APP_ROOT / "r1_pmv.sqlite3"),
            "etapa00_audit.sqlite3": sha256_file(
                RESULTADOS_DIR / "datos" / "etapa00-20261105" / "audit.sqlite3"
            ),
            "etapa01_audit.sqlite3": sha256_file(
                RESULTADOS_DIR / "datos" / "etapa01-20261109" / "audit.sqlite3"
            ),
        },
        "roles": list(Role.objects.order_by("code").values("id", "code", "name")),
        "accounts": [
            {
                "id": acc.id,
                "email": acc.email,
                "email_normalized": acc.email_normalized,
                "display_name": acc.display_name,
                "role_code": acc.role.code,
                "is_active": acc.is_active,
                "password_Redacted": "<REDACTED_TEST_SECRET>",
            }
            for acc in Account.objects.select_related("role").order_by("id")
        ],
        "fixtures": {
            "cash_register": {"id": register.id, "code": register.code},
            "category": {"id": category.id, "name": category.name},
            "product": {
                "id": product.id,
                "name": product.name,
                "barcode": product.barcode,
                "sale_price": str(product.sale_price),
            },
            "lot": {
                "id": lot.id,
                "number": lot.number,
                "available_quantity": lot.available_quantity,
                "expiration_date": lot.expiration_date.isoformat(),
            },
        },
    }

    manifest_path = db_path.parent / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, default=str, ensure_ascii=False))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    ensure_safe_db()
    argv = [
        "manage.py",
        "runserver",
        f"{args.host}:{args.port}",
        "--noreload",
        "--settings=audit02_settings",
    ]
    execute_from_command_line(argv)
    return 0


def cmd_proof(args: argparse.Namespace) -> int:
    challenge = args.challenge or f"nonce-{int(datetime.now().timestamp())}"
    url = f"http://{args.host}:{args.port}/"
    request = urllib.request.Request(url, headers={"X-Audit02-Challenge": challenge})
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = {
            "url": url,
            "status": response.status,
            "challenge": challenge,
            "proof": response.headers.get("X-Audit02-Proof"),
            "stage": response.headers.get("X-Audit02-Stage"),
            "cache_control": response.headers.get("Cache-Control"),
        }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    expected_suffix = f":{challenge}:audit.sqlite3"
    if not payload["proof"] or not payload["proof"].endswith(expected_suffix):
        raise SystemExit(2)
    return 0


def cmd_check(_args: argparse.Namespace) -> int:
    django.setup()
    ensure_safe_db()
    call_command("check")
    call_command("makemigrations", "--check", "--dry-run")
    return 0


def cmd_inspect(_args: argparse.Namespace) -> int:
    django.setup()
    db_path = ensure_safe_db()
    from cash.models import CashShift
    from django.contrib.sessions.models import Session
    from identity.models import Account, LoginAttempt
    from sales.models import SaleDraft

    state = {
        "database_path": str(db_path.relative_to(REPO_ROOT).as_posix()),
        "database_sha256": sha256_file(db_path),
        "accounts": [
            {
                "id": acc.id,
                "email": acc.email,
                "email_normalized": acc.email_normalized,
                "display_name": acc.display_name,
                "role_code": acc.role.code,
                "is_active": acc.is_active,
            }
            for acc in Account.objects.select_related("role").order_by("id")
        ],
        "login_attempts": list(
            LoginAttempt.objects.order_by("identifier").values(
                "identifier", "failures", "locked_until", "updated_at"
            )
        ),
        "active_sessions_count": Session.objects.count(),
        "open_shifts": list(
            CashShift.objects.filter(status=CashShift.Status.OPEN).values(
                "id", "cash_register__code", "seller__email", "status"
            )
        ),
        "active_drafts": list(
            SaleDraft.objects.values("id", "seller__email", "cash_shift_id", "status")
        ),
    }
    print(json.dumps(state, indent=2, default=str, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prepare = sub.add_parser("prepare", help="Prepara y migra la base aislada de Etapa 02.")
    p_prepare.add_argument("--reset", action="store_true", help="Recrea la base desde cero.")
    p_prepare.set_defaults(func=cmd_prepare)

    p_serve = sub.add_parser("serve", help="Levanta runserver aislado sin autoreload.")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", default=8767, type=int)
    p_serve.set_defaults(func=cmd_serve)

    p_proof = sub.add_parser("proof", help="Verifica el nonce de cabecera del servidor vivo.")
    p_proof.add_argument("--host", default="127.0.0.1")
    p_proof.add_argument("--port", default=8767, type=int)
    p_proof.add_argument("--challenge", default="")
    p_proof.set_defaults(func=cmd_proof)

    p_check = sub.add_parser("check", help="Ejecuta check y makemigrations --check --dry-run.")
    p_check.set_defaults(func=cmd_check)

    p_inspect = sub.add_parser("inspect", help="Inspecciona el estado ORM actual sin secretos.")
    p_inspect.set_defaults(func=cmd_inspect)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
