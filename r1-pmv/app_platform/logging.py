"""Logging guards: metadata may be logged, secrets and credentials may not."""
from __future__ import annotations

import logging
import re
import traceback


SENSITIVE_VALUE_PATTERNS = (
    re.compile(
        r'''(?ix)
        (
            ["']?
            (?:password|passwd|pwd|password1|password2|new_password|
               clave|contrasena|contraseña|token|secret|api[_-]?key|
               csrf|csrfmiddlewaretoken|csrftoken|session|sessionid|
               cookie|set-cookie)
            ["']?\s*(?:[:=]|\bis\b)\s*
            (?:\[\s*)?
        )
        (?:"[^"]*"|'[^']*'|[^\s,;&}\]]+)
        '''
    ),
    re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|basic)\s+)\S+"),
    re.compile(r"(?i)((?:sessionid|csrftoken)=)[^\s;,'\"]+"),
)


def redact_sensitive_text(text: object) -> str:
    """Redact credentials, tokens, cookies, and form secrets from log text."""
    rendered = str(text or "")
    for pattern in SENSITIVE_VALUE_PATTERNS:
        rendered = pattern.sub(r"\1[REDACTED]", rendered)
    return rendered


class RedactSensitiveDataFilter(logging.Filter):
    patterns = SENSITIVE_VALUE_PATTERNS

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            raw_args = ""
            if record.args:
                raw_args = f" args={record.args!r}"
            message = f"{record.msg!r}{raw_args}"
        record.msg = redact_sensitive_text(message)
        record.args = ()

        if record.exc_info:
            formatted = "".join(traceback.format_exception(*record.exc_info)).rstrip()
            record.exc_text = redact_sensitive_text(formatted)
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = redact_sensitive_text(record.exc_text)
        return True
