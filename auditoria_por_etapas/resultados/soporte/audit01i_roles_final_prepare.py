"""Add a separate set of fictional roles to the 01-I database for final-build UI checks."""
from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-I-20261115"
sys.path[:0] = [str(ROOT / "r1-pmv"), str(Path(__file__).resolve().parent)]
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01i_settings"
import django

django.setup()
from django.db import connection, transaction
from identity.models import Account, Role

assert Path(connection.settings_dict["NAME"]).resolve() == (DATA / "audit.sqlite3").resolve()
destination = DATA / ".roles-final.json"
if destination.exists():
    raise SystemExit("Las credenciales ficticias de este corte ya existen")
specs = {
    "admin": ("admin.final01i@ejemplo.invalid", Role.Code.ADMIN, "Admin 01I", True),
    "warehouse": ("almacen.final01i@ejemplo.invalid", Role.Code.WAREHOUSE, "Almacenero 01I final", True),
    "seller": ("vendedor.final01i@ejemplo.invalid", Role.Code.SELLER, "Vendedor 01I final", True),
    "inactive": ("inactiva.final01i@ejemplo.invalid", Role.Code.SELLER, "Inactiva 01I final", False),
}
credentials = {}
with transaction.atomic():
    for key, (email, role_code, name, active) in specs.items():
        if Account.objects.filter(email_normalized=Account.normalize_email(email)).exists():
            raise RuntimeError("La cuenta ficticia del corte ya existe")
        password = secrets.token_urlsafe(24)
        account = Account.objects.create_user(
            email=email, password=password, display_name=name,
            role=Role.objects.get(code=role_code), is_active=active,
        )
        credentials[key] = {"email": email, "password": password, "role": role_code, "account_id": str(account.pk)}
destination.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding="utf-8")
print("Creadas cuatro cuentas ficticias para la revalidación final")
