"""Aggregate privacy-relevant state without recording identifiers or secrets."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "r1-pmv"), str(Path(__file__).resolve().parent)]
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01h_settings"
import django

django.setup()
from django.db import connection
from identity.models import IdentityAuditEvent, LoginAttempt

own = ROOT / "auditoria_por_etapas/resultados/datos/01-H-20261115/audit.sqlite3"
assert Path(connection.settings_dict["NAME"]).resolve() == own.resolve()
events = list(IdentityAuditEvent.objects.filter(action__in=["LOGIN_FAILED", "LOGIN_LOCKED"]).values("actor_identifier", "metadata"))
attempts = LoginAttempt.objects.all()
result = {
    "alcance": "solo filas ficticias 01-H; consultas agregadas",
    "failed_or_locked_events": len(events),
    "events_with_nonempty_identifier": sum(bool(e["actor_identifier"]) for e in events),
    "events_with_at_sign_in_identifier": sum("@" in e["actor_identifier"] for e in events),
    "events_with_account_exists_metadata": sum("account_exists" in (e["metadata"] or {}) for e in events),
    "events_with_account_active_metadata": sum("account_active" in (e["metadata"] or {}) for e in events),
    "attempts": attempts.count(),
    "attempts_with_64_character_identifier": sum(len(identifier) == 64 for identifier in attempts.values_list("identifier", flat=True)),
    "attempt_model_columns": [f.name for f in LoginAttempt._meta.fields],
    "outputs_include_identifiers": False,
}
path = ROOT / "auditoria_por_etapas/resultados/evidencias/01-H-20261115/privacidad-agregada.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
