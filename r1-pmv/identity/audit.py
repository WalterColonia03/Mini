"""Auditoria tecnica transaccional y correlacion de request_id para identity."""
from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
import uuid
from datetime import timezone as dt_timezone
from typing import Any

from django.db import transaction
from django.utils import timezone

from app_platform.logging import redact_sensitive_text

audit_logger = logging.getLogger("identity.audit")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:password|passwd|pwd|clave|contrasena|contraseña|secret|token|cookie|csrf|authorization|api[_-]?key|(?:^|[_-])session(?:$|[_-]?(?:id|key|token|data|secret|cookie)))"
)
_current_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "identity_request_id",
    default="",
)


def normalize_request_id(candidate: str | None) -> str:
    raw = (candidate or "").strip()
    if raw and _REQUEST_ID_RE.fullmatch(raw):
        return raw
    return uuid.uuid4().hex


def current_request_id(explicit: str | None = None) -> str:
    raw = (explicit or "").strip()
    if raw and _REQUEST_ID_RE.fullmatch(raw):
        return raw
    active = _current_request_id.get()
    if active:
        return active
    return f"svc-{uuid.uuid4().hex[:24]}"


def bind_request_id(request_id: str) -> contextvars.Token[str]:
    return _current_request_id.set(normalize_request_id(request_id))


def reset_request_id(token: contextvars.Token[str]) -> None:
    _current_request_id.reset(token)


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only non-sensitive structured metadata, truncating arbitrary strings."""
    if not metadata:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        key_str = str(key)[:64]
        if _SENSITIVE_KEY_RE.search(key_str):
            cleaned[key_str] = "[REDACTED]"
            continue
        if isinstance(value, (bool, int)) or value is None:
            cleaned[key_str] = value
        elif isinstance(value, (list, tuple)):
            cleaned[key_str] = [redact_sensitive_text(str(item))[:120] for item in value[:20]]
        elif isinstance(value, dict):
            cleaned[key_str] = sanitize_metadata(value)
        else:
            cleaned[key_str] = redact_sensitive_text(str(value))[:200]
    return cleaned


def _emit_external_event(payload: dict[str, Any]) -> None:
    try:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        level = logging.WARNING if payload.get("outcome") in {"REJECTED", "LOCKED", "ERROR"} else logging.INFO
        audit_logger.log(level, "identity_audit %s", redact_sensitive_text(serialized))
    except Exception as exc:
        # Logging failures must never subvert already-decided security outcomes; record sanitized fallback.
        try:
            fallback = redact_sensitive_text(
                f"identity_audit_log_failure action={payload.get('action')} "
                f"outcome={payload.get('outcome')} request_id={payload.get('request_id')} "
                f"error={exc.__class__.__name__}"
            )
            sys.stderr.write(fallback + "\n")
        except Exception:
            pass


def record_transactional_event(
    *,
    action: str,
    target_type: str,
    outcome: str,
    actor=None,
    actor_identifier: str = "",
    target_id: str = "",
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any:
    """Persist an IdentityAuditEvent in the active transaction and log only on commit."""
    from .models import IdentityAuditEvent

    req_id = current_request_id(request_id)
    resolved_identifier = actor_identifier or getattr(actor, "email_normalized", "") or ""
    clean_meta = sanitize_metadata(metadata)
    now = timezone.now()
    event = IdentityAuditEvent.objects.create(
        occurred_at=now,
        actor=actor if getattr(actor, "pk", None) else None,
        actor_identifier=resolved_identifier[:254],
        action=action[:64],
        target_type=target_type[:64],
        target_id=str(target_id)[:128],
        outcome=outcome,
        request_id=req_id,
        metadata=clean_meta,
    )
    payload = {
        "event_id": str(event.pk),
        "occurred_at_utc": now.astimezone(dt_timezone.utc).isoformat(),
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "actor_identifier": event.actor_identifier or None,
        "action": event.action,
        "target_type": event.target_type,
        "target_id": event.target_id or None,
        "outcome": event.outcome,
        "request_id": event.request_id,
        "metadata": clean_meta,
    }
    transaction.on_commit(lambda p=payload: _emit_external_event(p))
    return event


def safe_record_rejection_event(
    *,
    action: str,
    target_type: str,
    outcome: str = "REJECTED",
    actor=None,
    actor_identifier: str = "",
    target_id: str = "",
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    persist_db: bool = True,
) -> None:
    """Record a rejected access/mutation event safely without ever granting access on failure."""
    from .models import IdentityAuditEvent

    req_id = current_request_id(request_id)
    resolved_identifier = actor_identifier or getattr(actor, "email_normalized", "") or ""
    clean_meta = sanitize_metadata(metadata)
    now = timezone.now()
    payload = {
        "occurred_at_utc": now.astimezone(dt_timezone.utc).isoformat(),
        "actor_id": str(getattr(actor, "pk", "")) or None,
        "actor_identifier": resolved_identifier[:254] or None,
        "action": action[:64],
        "target_type": target_type[:64],
        "target_id": str(target_id)[:128] or None,
        "outcome": outcome,
        "request_id": req_id,
        "metadata": clean_meta,
    }
    if persist_db:
        try:
            conn = transaction.get_connection()
            if not conn.needs_rollback:
                event = IdentityAuditEvent.objects.create(
                    occurred_at=now,
                    actor=actor if getattr(actor, "pk", None) else None,
                    actor_identifier=resolved_identifier[:254],
                    action=action[:64],
                    target_type=target_type[:64],
                    target_id=str(target_id)[:128],
                    outcome=outcome,
                    request_id=req_id,
                    metadata=clean_meta,
                )
                payload["event_id"] = str(event.pk)
        except Exception as exc:
            clean_meta = {**clean_meta, "audit_persist_error": exc.__class__.__name__}
            payload["metadata"] = clean_meta

    _emit_external_event(payload)
