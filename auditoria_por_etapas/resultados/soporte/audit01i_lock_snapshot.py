"""Capture only synthetic ADMIN lock state, without exposing credentials."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-I-20261115"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-I-20261115"
sys.path[:0] = [str(ROOT / "r1-pmv"), str(Path(__file__).resolve().parent)]
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01i_settings"
import django

django.setup()
from django.db import connection
from django.utils.crypto import salted_hmac
from identity.models import Account, IdentityAuditEvent, LoginAttempt

assert Path(connection.settings_dict["NAME"]).resolve() == (DATA / "audit.sqlite3").resolve()
parser = argparse.ArgumentParser()
parser.add_argument("--label", choices=("antes-espera", "despues-espera"), required=True)
args = parser.parse_args()
fixture = json.loads((DATA / ".credentials.json").read_text(encoding="utf-8"))["admin"]
identifier = salted_hmac("identity.login.throttle", Account.normalize_email(fixture["email"]), algorithm="sha256").hexdigest()
attempt = LoginAttempt.objects.get(pk=identifier)
events = IdentityAuditEvent.objects.filter(actor_id=fixture["account_id"], action="LOGIN_LOCKED").order_by("occurred_at")
initial = next((event for event in events if not (event.metadata or {}).get("already_locked")), None)
now = datetime.now(timezone.utc)
result = {
    "label": args.label,
    "capturado_utc": now.isoformat(),
    "fallos": attempt.failures,
    "locked_until_utc": attempt.locked_until.astimezone(timezone.utc).isoformat() if attempt.locked_until else None,
    "segundos_restantes": round((attempt.locked_until - now).total_seconds(), 3) if attempt.locked_until else None,
    "evento_quinto_fallo_utc": initial.occurred_at.astimezone(timezone.utc).isoformat() if initial else None,
    "identificadores_incluidos": False,
}
path = OUT / (args.label + ".json")
if path.exists():
    raise SystemExit("No se sobrescribe evidencia existente")
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
