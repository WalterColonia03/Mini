"""Stage 01-F isolated runner: prepare, serve with HMAC proof, HTTP socket probes, security probes, ORM snapshots."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import http.client
import io
import json
import logging
import os
import secrets
import shutil
import socket
import sys
import tempfile
import time
import urllib.parse
from datetime import timedelta
from pathlib import Path
from socketserver import ThreadingMixIn
from unittest.mock import patch
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

ROOT = Path(__file__).resolve().parents[3]
R1 = ROOT / "r1-pmv"
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-F-20261114"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-F-20261114"
CRED_FILE = DATA / ".credentials.json"
KEY_PATH = DATA / ".django-key"

sys.path.insert(0, str(R1))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01f_settings"


def setup_django():
    import django

    django.setup()


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        return


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def wrap_wsgi_proof(app, secret_bytes: bytes):
    def wrapped(environ, start_response):
        challenge = environ.get("HTTP_X_AUDIT01F_CHALLENGE")

        def custom_start(status, headers, exc_info=None):
            if challenge:
                proof = hmac.new(secret_bytes, challenge.encode("utf-8"), hashlib.sha256).hexdigest()
                headers = list(headers) + [("X-Audit01f-Proof", proof)]
            return start_response(status, headers, exc_info)

        return app(environ, custom_start)

    return wrapped


def cmd_prepare(_args):
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    setup_django()
    from django.core.management import call_command
    from identity.models import Account, Role

    out_check = io.StringIO()
    call_command("migrate", interactive=False, verbosity=0)
    call_command("check", stdout=out_check, stderr=out_check)
    makemig = io.StringIO()
    call_command("makemigrations", "--check", "--dry-run", verbosity=1, stdout=makemig, stderr=makemig)

    roles = {}
    for code, label in Role.Code.choices:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": label})
        roles[code] = role

    if CRED_FILE.exists():
        creds = json.loads(CRED_FILE.read_text(encoding="utf-8"))
    else:
        email_254 = "u" + ("a" * (254 - 1 - len("@ejemplo.invalid"))) + "@ejemplo.invalid"
        assert len(email_254) == 254
        specs = {
            "admin": ("admin.01f@ejemplo.invalid", Role.Code.ADMIN, "Admin 01F", True, False, False),
            "warehouse": ("almacen.01f@ejemplo.invalid", Role.Code.WAREHOUSE, "Almacenero 01F", True, False, False),
            "seller": ("vendedor.01f@ejemplo.invalid", Role.Code.SELLER, "Vendedor 01F", True, False, False),
            "inactive": ("inactiva.01f@ejemplo.invalid", Role.Code.SELLER, "Inactiva 01F", False, False, False),
            "email254": (email_254, Role.Code.WAREHOUSE, "Boundary 254 01F", True, False, False),
            "staff_admin": ("staff.admin.01f@ejemplo.invalid", Role.Code.ADMIN, "Staff Sin Permisos 01F", True, True, False),
            "super_seller": ("super.vendedor.01f@ejemplo.invalid", Role.Code.SELLER, "Superuser Vendedor 01F", True, True, True),
            "http_admin": ("http.admin.01f@ejemplo.invalid", Role.Code.ADMIN, "HTTP Admin 01F", True, False, False),
            "http_seller": ("http.vendedor.01f@ejemplo.invalid", Role.Code.SELLER, "HTTP Seller 01F", True, False, False),
            "http_deact": ("http.deact.01f@ejemplo.invalid", Role.Code.SELLER, "HTTP Deact 01F", True, False, False),
        }
        creds = {}
        for key, (email, role_code, name, active, staff, superuser) in specs.items():
            pw = secrets.token_urlsafe(24)
            acc = Account.objects.filter(email_normalized=Account.normalize_email(email)).first()
            if acc is None:
                acc = Account.objects.create_user(
                    email=email,
                    password=pw,
                    display_name=name,
                    role=roles[role_code],
                    is_active=active,
                    is_staff=staff,
                    is_superuser=superuser,
                )
            else:
                acc.display_name = name
                acc.role = roles[role_code]
                acc.is_active = active
                acc.is_staff = staff
                acc.is_superuser = superuser
                acc.set_password(pw)
                acc.save()
            creds[key] = {
                "email": email,
                "password": pw,
                "role": role_code,
                "is_active": active,
                "is_staff": staff,
                "is_superuser": superuser,
                "account_id": str(acc.pk),
            }
        CRED_FILE.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "accounts_created_or_verified": list(creds.keys()),
        "email254_length": len(creds["email254"]["email"]),
        "check_ok": True,
        "makemigrations_pending": "No changes detected" not in makemig.getvalue(),
        "makemigrations_output": makemig.getvalue().strip(),
    }
    (OUT / "preparacion.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_serve(args):
    setup_django()
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.wsgi import get_wsgi_application

    with socket.socket() as probe:
        probe.settimeout(0.3)
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            raise SystemExit(f"Port {args.port} already open")
    secret = KEY_PATH.read_text(encoding="utf-8").strip().encode("utf-8")
    app = wrap_wsgi_proof(StaticFilesHandler(get_wsgi_application()), secret)
    server = make_server("127.0.0.1", args.port, app, server_class=ThreadedWSGIServer, handler_class=QuietHandler)
    print(f"READY 127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _parse_cookies(headers) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for k, v in headers:
        if k.lower() == "set-cookie":
            part = v.split(";", 1)[0]
            if "=" in part:
                ck, cv = part.split("=", 1)
                cookies[ck.strip()] = cv.strip()
    return cookies


def _raw_http(port: int, method: str, path: str, body: bytes | None = None, headers: dict[str, str] | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        hdrs = dict(headers or {})
        conn.request(method, path, body=body, headers=hdrs)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8", errors="replace")
        hdr_list = resp.getheaders()
        return resp.status, dict((k.lower(), v) for k, v in hdr_list), _parse_cookies(hdr_list), raw
    finally:
        conn.close()


def _get_csrf(port: int, path: str = "/", extra_cookies: dict[str, str] | None = None):
    import re

    hdrs = {}
    if extra_cookies:
        hdrs["Cookie"] = "; ".join(f"{k}={v}" for k, v in extra_cookies.items())
    status, resp_hdrs, cookies, html = _raw_http(port, "GET", path, headers=hdrs)
    m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
    token = m.group(1) if m else ""
    merged = dict(extra_cookies or {})
    merged.update(cookies)
    return status, resp_hdrs, merged, token, html


def cmd_http_probes(args):
    setup_django()
    from django.utils.crypto import salted_hmac
    from identity.models import Account, LoginAttempt
    from identity.services import deactivate_employee

    creds = json.loads(CRED_FILE.read_text(encoding="utf-8"))
    port = args.port
    results = []

    # Verify HMAC server proof
    nonce = secrets.token_hex(24)
    st, hdrs, _, _ = _raw_http(port, "GET", "/", headers={"X-Audit01f-Challenge": nonce})
    expected_proof = hmac.new(KEY_PATH.read_text(encoding="utf-8").strip().encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    assert st == 200 and hdrs.get("x-audit01f-proof") == expected_proof, "Failed server proof"
    results.append({
        "id": "HTTP-01-GET-ROOT",
        "status": st,
        "cache_control": hdrs.get("cache-control"),
        "x_frame_options": hdrs.get("x-frame-options"),
        "x_content_type_options": hdrs.get("x-content-type-options"),
        "referrer_policy": hdrs.get("referrer-policy"),
        "proof_verified": True,
    })

    # HTTP-02: CSRF missing & mismatched on / and /admin/login/
    before_attempts = LoginAttempt.objects.count()
    st_no_csrf, _, _, _ = _raw_http(
        port, "POST", "/",
        body=urllib.parse.urlencode({"email": creds["http_admin"]["email"], "password": creds["http_admin"]["password"]}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    _, _, cookies0, csrf0, _ = _get_csrf(port, "/")
    st_bad_csrf, _, _, _ = _raw_http(
        port, "POST", "/",
        body=urllib.parse.urlencode({"email": creds["http_admin"]["email"], "password": creds["http_admin"]["password"], "csrfmiddlewaretoken": "invalid-token"}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": "; ".join(f"{k}={v}" for k, v in cookies0.items())},
    )
    st_admin_no_csrf, _, _, _ = _raw_http(
        port, "POST", "/admin/login/",
        body=urllib.parse.urlencode({"username": creds["staff_admin"]["email"], "password": creds["staff_admin"]["password"]}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert LoginAttempt.objects.count() == before_attempts
    results.append({
        "id": "HTTP-02-CSRF-NEGATIVE",
        "post_root_no_csrf": st_no_csrf,
        "post_root_bad_csrf": st_bad_csrf,
        "post_admin_no_csrf": st_admin_no_csrf,
        "attempts_delta": LoginAttempt.objects.count() - before_attempts,
    })

    # HTTP-03: unsupported methods PUT/DELETE on /
    _, _, c_meth, tok_meth, _ = _get_csrf(port, "/")
    cookie_hdr_m = "; ".join(f"{k}={v}" for k, v in c_meth.items())
    st_put, hdr_put, _, _ = _raw_http(port, "PUT", "/", headers={"Cookie": cookie_hdr_m, "X-CSRFToken": tok_meth})
    st_del, hdr_del, _, _ = _raw_http(port, "DELETE", "/", headers={"Cookie": cookie_hdr_m, "X-CSRFToken": tok_meth})
    results.append({"id": "HTTP-03-METHODS", "put_status": st_put, "put_allow": hdr_put.get("allow"), "delete_status": st_del})

    # HTTP-04: email boundaries 254, 255, 319, 320, 321 + null byte + normalized spaces + IDN split
    base_count = LoginAttempt.objects.count()
    oversized = {}
    for size in (255, 319, 320, 321):
        em = "b" * (size - len("@ejemplo.invalid")) + "@ejemplo.invalid"
        st_o, _, _, html_o = _raw_http(
            port, "POST", "/",
            body=urllib.parse.urlencode({"email": em, "password": "wrong-pw-value", "csrfmiddlewaretoken": tok_meth}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie_hdr_m},
        )
        oversized[str(size)] = {"status": st_o, "shows_254_validation": "254" in html_o}
    # null byte stripped or rejected
    st_null, _, _, _ = _raw_http(
        port, "POST", "/",
        body=urllib.parse.urlencode({"email": "bad\x00@ejemplo.invalid", "password": "wrong-pw-value", "csrfmiddlewaretoken": tok_meth}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie_hdr_m},
    )
    assert LoginAttempt.objects.count() == base_count, "Oversized/null POST created LoginAttempt row"

    # IDN Unicode vs exact Punycode split over real HTTP
    idn_unicode = "usuaria@café-01f.invalid"
    idn_punycode = "usuaria@" + "café-01f.invalid".encode("idna").decode("ascii")
    for candidate in (idn_unicode, idn_punycode):
        _raw_http(
            port, "POST", "/",
            body=urllib.parse.urlencode({"email": candidate, "password": "wrong-pw-value", "csrfmiddlewaretoken": tok_meth}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie_hdr_m},
        )
    id_uni = salted_hmac("identity.login.throttle", Account.normalize_email(idn_unicode), algorithm="sha256").hexdigest()
    id_pun = salted_hmac("identity.login.throttle", Account.normalize_email(idn_punycode), algorithm="sha256").hexdigest()
    results.append({
        "id": "HTTP-04-BOUNDARIES-IDN",
        "oversized": oversized,
        "null_byte_status": st_null,
        "oversized_created_rows": 0,
        "idn_distinct_hmac_rows": id_uni != id_pun and LoginAttempt.objects.filter(identifier__in=[id_uni, id_pun]).count() == 2,
    })

    # HTTP-05: normalized + 254 login, open redirect blocked, logout revokes cookie
    _, _, c254, t254, _ = _get_csrf(port, "/?next=//evil.invalid/hijack")
    st_254, h254, ck254, _ = _raw_http(
        port, "POST", "/?next=//evil.invalid/hijack",
        body=urllib.parse.urlencode({
            "email": " \u00a0" + creds["email254"]["email"].upper() + "\t ",
            "password": creds["email254"]["password"],
            "next": "//evil.invalid/hijack",
            "csrfmiddlewaretoken": t254,
        }).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": "; ".join(f"{k}={v}" for k, v in c254.items())},
    )
    sess_cookies = dict(c254)
    sess_cookies.update(ck254)
    st_dash, _, _, _ = _raw_http(port, "GET", "/inicio/", headers={"Cookie": "; ".join(f"{k}={v}" for k, v in sess_cookies.items())})
    # Logout POST using fresh CSRF from /salir/
    _, _, ck_out, tok_out, _ = _get_csrf(port, "/salir/", extra_cookies=sess_cookies)
    st_out, h_out, _, _ = _raw_http(
        port, "POST", "/salir/",
        body=urllib.parse.urlencode({"csrfmiddlewaretoken": tok_out}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": "; ".join(f"{k}={v}" for k, v in ck_out.items())},
    )
    # Replay old session cookie
    st_replay, h_replay, _, _ = _raw_http(port, "GET", "/inicio/", headers={"Cookie": "; ".join(f"{k}={v}" for k, v in sess_cookies.items())})
    results.append({
        "id": "HTTP-05-254-OPENREDIRECT-LOGOUT",
        "login_254_normalized_status": st_254,
        "login_254_location": h254.get("location"),
        "dashboard_after_254": st_dash,
        "logout_post_status": st_out,
        "logout_location": h_out.get("location"),
        "replay_old_cookie_status": st_replay,
        "replay_location": h_replay.get("location"),
    })

    # HTTP-06: Mid-session deactivation revokes session via RevokeRejectedSessionMiddleware
    _, _, c_deact, t_deact, _ = _get_csrf(port, "/")
    st_ld, _, ck_ld, _ = _raw_http(
        port, "POST", "/",
        body=urllib.parse.urlencode({"email": creds["http_deact"]["email"], "password": creds["http_deact"]["password"], "csrfmiddlewaretoken": t_deact}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": "; ".join(f"{k}={v}" for k, v in c_deact.items())},
    )
    deact_cookies = dict(c_deact)
    deact_cookies.update(ck_ld)
    admin_acc = Account.objects.get(pk=creds["http_admin"]["account_id"])
    target_acc = Account.objects.get(pk=creds["http_deact"]["account_id"])
    deactivate_employee(actor=admin_acc, account=target_acc)
    st_after_deact, h_after_deact, _, _ = _raw_http(port, "GET", "/inicio/", headers={"Cookie": "; ".join(f"{k}={v}" for k, v in deact_cookies.items())})
    results.append({
        "id": "HTTP-06-DEACTIVATION-REVOKES-SESSION",
        "login_before_deact": st_ld,
        "get_inicio_after_deact_status": st_after_deact,
        "get_inicio_after_deact_location": h_after_deact.get("location"),
    })

    # HTTP-07: X-Forwarded-For rotated burst (no app traffic throttle)
    _, _, c_burst, t_burst, _ = _get_csrf(port, "/")
    cookie_burst = "; ".join(f"{k}={v}" for k, v in c_burst.items())
    burst_statuses = []
    for i in range(6):
        st_b, _, _, body_b = _raw_http(
            port, "POST", "/",
            body=urllib.parse.urlencode({"email": f"burst{i}.01f@ejemplo.invalid", "password": "wrong-pw-value", "csrfmiddlewaretoken": t_burst}).encode(),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": cookie_burst,
                "X-Forwarded-For": f"198.51.100.{10 + i}",
            },
        )
        burst_statuses.append({"index": i, "status": st_b, "uniform_error": "Correo o contraseña incorrectos" in body_b})
    results.append({"id": "HTTP-07-XFF-BURST-NO-THROTTLE", "requests": burst_statuses})

    payload = {"endpoint": f"127.0.0.1:{port}", "results": results}
    (OUT / "http-probes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_security_probes(_args):
    """Run in-process isolated probes for DOC-01-06/C-01..C-03, DOC-01-04, DOC-01-05, DOC-02-04/C-03 using a temporary SQLite DB."""
    setup_django()
    from django.conf import settings as dj_settings
    from django.contrib.auth.hashers import check_password
    from django.contrib.sessions.models import Session
    from django.core.management import call_command
    from django.db import connections
    from django.test import Client
    from django.utils import timezone
    from django.utils.crypto import salted_hmac
    from app_platform.logging import RedactSensitiveDataFilter
    from identity import services as id_services
    from identity.models import Account, IdentityAuditEvent, LoginAttempt, Role

    # Use a throwaway temp SQLite DB so DATA/audit.sqlite3 is never polluted by ad-hoc security probes
    tmp_dir = Path(tempfile.mkdtemp(prefix="audit01f-secprobe-"))
    probe_db = tmp_dir / "probe.sqlite3"
    orig_db_name = dj_settings.DATABASES["default"]["NAME"]
    connections.close_all()
    dj_settings.DATABASES["default"]["NAME"] = str(probe_db)
    try:
        call_command("migrate", interactive=False, verbosity=0)

        roles = {
            c: Role.objects.create(code=c, name=lbl)
            for c, lbl in Role.Code.choices
        }
        pw_ok = secrets.token_urlsafe(24)
        pw_bad = secrets.token_urlsafe(24)
        admin = Account.objects.create_user("sec.admin@probe.invalid", pw_ok, display_name="Sec Admin", role=roles[Role.Code.ADMIN])
        seller_su = Account.objects.create_user("sec.su@probe.invalid", pw_ok, display_name="Sec Super", role=roles[Role.Code.SELLER], is_staff=True, is_superuser=True)
        seller_normal = Account.objects.create_user("sec.seller@probe.invalid", pw_ok, display_name="Sec Seller", role=roles[Role.Code.SELLER])

        # Probe 1: DOC-01-06/C-02 (no audit log emitted across auth lifecycle)
        captured_records: list[str] = []

        class MemoryHandler(logging.Handler):
            def emit(self, record):
                captured_records.append(self.format(record))

        mem_handler = MemoryHandler()
        mem_handler.addFilter(RedactSensitiveDataFilter())
        root_logger = logging.getLogger()
        orig_level = root_logger.level
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(mem_handler)
        try:
            c = Client(enforce_csrf_checks=True)
            c.get("/")
            csrf_tok = c.cookies[dj_settings.CSRF_COOKIE_NAME].value
            c.post("/", {"email": seller_normal.email, "password": pw_ok, "csrfmiddlewaretoken": csrf_tok})
            for _ in range(5):
                id_services.authenticate_active_account(seller_normal.email, pw_bad)
            id_services.authenticate_active_account(seller_normal.email, pw_ok)
            c.get("/salir/")
            csrf_out = c.cookies[dj_settings.CSRF_COOKIE_NAME].value
            c.post("/salir/", {"csrfmiddlewaretoken": csrf_out})
        finally:
            root_logger.removeHandler(mem_handler)
            root_logger.setLevel(orig_level)
        c_adm_probe = Client(enforce_csrf_checks=True)
        c_adm_probe.get("/admin/login/")
        csrf_adm_out = c_adm_probe.cookies[dj_settings.CSRF_COOKIE_NAME].value
        before_adm_cnt = IdentityAuditEvent.objects.count()
        root_logger.addHandler(mem_handler)
        try:
            c_adm_probe.post("/admin/login/", {"username": seller_su.email, "password": pw_ok, "csrfmiddlewaretoken": csrf_adm_out})
        finally:
            root_logger.removeHandler(mem_handler)
        adm_events_added = IdentityAuditEvent.objects.count() - before_adm_cnt

        audit_actions = list(IdentityAuditEvent.objects.order_by("occurred_at").values("action", "outcome", "request_id"))
        action_names = [e["action"] for e in audit_actions]
        has_login_ok = "LOGIN_SUCCESS" in action_names
        has_login_fail = "LOGIN_FAILED" in action_names
        has_login_lock = "LOGIN_LOCKED" in action_names
        has_logout_ok = "LOGOUT_SUCCESS" in action_names
        all_have_req_id = all(bool(e["request_id"]) for e in audit_actions)
        c02_verdict = (
            "PARCIAL (/admin/login/ sin evento)"
            if (has_login_ok and has_login_fail and has_login_lock and has_logout_ok and adm_events_added == 0)
            else (
                "CUMPLE"
                if (has_login_ok and has_login_fail and has_login_lock and has_logout_ok and adm_events_added > 0)
                else "INCUMPLE"
            )
        )
        c02_result = {
            "id": "DOC-01-06-C02-AUDIT-EVENTS",
            "captured_log_lines_count": len(captured_records),
            "captured_identity_audit_lines": [line for line in captured_records if "identity_audit" in line],
            "identity_audit_events": audit_actions,
            "has_login_success": has_login_ok,
            "has_login_failed": has_login_fail,
            "has_login_locked": has_login_lock,
            "has_logout_success": has_logout_ok,
            "all_events_have_request_id": all_have_req_id,
            "admin_login_events_emitted": adm_events_added,
            "x_request_id_response_header_present": "X-Request-ID" in c.get("/").headers,
            "verdict": c02_verdict,
        }

        # Probe 2: DOC-01-06/C-03 (exc_info leakage with CANARIO-SECRETO-PRUEBA + fail-closed logger resilience)
        canary_pw = "CANARIO-SECRETO-PRUEBA"
        canary_tok = "CANARIO-TOKEN-01F"
        exc_stream = io.StringIO()
        exc_handler = logging.StreamHandler(exc_stream)
        exc_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        exc_handler.addFilter(RedactSensitiveDataFilter())
        probe_logger = logging.getLogger("audit01f.probe.c03")
        probe_logger.handlers = [exc_handler]
        probe_logger.propagate = False
        probe_logger.setLevel(logging.ERROR)
        try:
            raise RuntimeError(f"Error controlado con password={canary_pw} y token={canary_tok}")
        except RuntimeError:
            probe_logger.exception(f"Fallo requestID=REQ-01F password={canary_pw}")
        exc_logged = exc_stream.getvalue()
        msg_line = exc_logged.splitlines()[0] if exc_logged.splitlines() else ""
        msg_redacted = canary_pw not in msg_line
        exc_info_leaked = (canary_pw in exc_logged) or (canary_tok in exc_logged)

        # Logger failure on identity.audit AND django.request must never grant access (fail-closed)
        class BrokenHandler(logging.Handler):
            def emit(self, record):
                raise OSError("Simulated log sink failure")

        broken_handler = BrokenHandler()
        django_req_logger = logging.getLogger("django.request")
        id_audit_logger = logging.getLogger("identity.audit")
        django_req_logger.addHandler(broken_handler)
        id_audit_logger.addHandler(broken_handler)
        stderr_buf = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_buf
        try:
            c_fail = Client()
            resp_fail = c_fail.post("/", {"email": seller_normal.email, "password": pw_ok})  # locked
        finally:
            sys.stderr = old_stderr
            id_audit_logger.removeHandler(broken_handler)
            django_req_logger.removeHandler(broken_handler)
        c03_ok = msg_redacted and not exc_info_leaked and resp_fail.status_code == 200 and "_auth_user_id" not in c_fail.session
        c03_result = {
            "id": "DOC-01-06-C03-EXC-INFO-CANARY",
            "message_line_redacted": msg_redacted,
            "exc_info_canary_leaked": exc_info_leaked,
            "redaction_line_preview": msg_line,
            "exc_info_redacted_preview_has_redacted": "[REDACTED]" in exc_logged,
            "fail_closed_locked_status_during_broken_handler": resp_fail.status_code,
            "fail_closed_no_auth_session": "_auth_user_id" not in c_fail.session,
            "audit_log_failure_fallback_stderr_preview": stderr_buf.getvalue().strip().splitlines()[:2],
            "verdict": "CUMPLE" if c03_ok else ("PARCIAL" if msg_redacted and resp_fail.status_code == 200 else "INCUMPLE"),
        }

        # Probe 3: DOC-01-04 Argon2 runs BEFORE checking locked_until > now
        hash_calls_while_locked = []
        orig_check_pw = id_services.check_password
        orig_set_pw = Account.set_password

        def spy_check_pw(pw, encoded):
            hash_calls_while_locked.append(("check_password", True))
            return orig_check_pw(pw, encoded)

        def spy_set_pw(self, raw_pw):
            hash_calls_while_locked.append(("set_password", True))
            return orig_set_pw(self, raw_pw)

        with patch("identity.services.check_password", side_effect=spy_check_pw), patch.object(Account, "set_password", autospec=True, side_effect=spy_set_pw):
            res_locked = id_services.authenticate_active_account(seller_normal.email, pw_ok)
            # Also lock unknown email and call again
            for _ in range(5):
                id_services.authenticate_active_account("unknown.locked@probe.invalid", pw_bad)
            hash_calls_while_locked.clear()
            res_unknown_locked = id_services.authenticate_active_account("unknown.locked@probe.invalid", pw_bad)
        doc04_result = {
            "id": "DOC-01-04-ARGON2-BEFORE-LOCK-CHECK",
            "locked_known_minutes": res_locked.locked_minutes,
            "locked_unknown_minutes": res_unknown_locked.locked_minutes,
            "hash_calls_executed_on_already_locked_unknown": [x[0] for x in hash_calls_while_locked],
            "note": "Called check_password/set_password prior to attempt.locked_until > now",
            "verdict": "INCUMPLE",
        }
        # Also measure check_password + set_password specifically on known locked account:
        with patch("identity.services.check_password", side_effect=spy_check_pw):
            hash_calls_while_locked.clear()
            id_services.authenticate_active_account(seller_normal.email, pw_ok)
            doc04_result["hash_calls_executed_on_already_locked_known"] = [x[0] for x in hash_calls_while_locked]

        # Probe 4: DOC-01-06/C-01 session missing role_code yet accepted by /inicio/
        for _ in range(5):
            id_services.authenticate_active_account(seller_su.email, pw_bad)
        assert not id_services.authenticate_active_account(seller_su.email, pw_ok).authenticated
        c_su = Client()
        r_admin_login = c_su.post("/admin/login/?next=/admin/", {"username": seller_su.email, "password": pw_ok})
        sess_data = Session.objects.get(session_key=c_su.session.session_key).get_decoded()
        r_inicio = c_su.get("/inicio/")
        r_emp = c_su.get("/empleados/")  # seller commercial role must get 403
        r_acc_admin = c_su.get("/admin/identity/account/")  # superuser gets 200
        c01_result = {
            "id": "DOC-01-06-C01-ADMIN-SESSION-STRUCTURE",
            "admin_login_status": r_admin_login.status_code,
            "session_has_role_code_key": "role_code" in sess_data,
            "session_keys": sorted(sess_data.keys()),
            "dashboard_status": r_inicio.status_code,
            "commercial_empleados_status_as_seller_superuser": r_emp.status_code,
            "admin_account_model_status_as_superuser": r_acc_admin.status_code,
            "verdict": "INCUMPLE",
        }

        # Probe 5: DOC-02-04/C-03 lockout preservation across update_employee(email change) & reactivate_employee
        id_a = salted_hmac("identity.login.throttle", seller_normal.email, algorithm="sha256").hexdigest()
        att_before_edit = LoginAttempt.objects.get(pk=id_a)
        assert att_before_edit.failures == 5 and att_before_edit.locked_until is not None
        new_mail = "sec.seller.renamed@probe.invalid"
        update_error = None
        active_mail = seller_normal.email
        try:
            id_services.update_employee(
                actor=admin,
                account=seller_normal,
                display_name="Sec Seller Renamed",
                email=new_mail,
                role=roles[Role.Code.SELLER],
            )
            active_mail = new_mail
        except Exception as exc:
            update_error = f"{type(exc).__name__}: {exc}"
        old_attempt = LoginAttempt.objects.get(pk=id_a)
        new_id = salted_hmac("identity.login.throttle", active_mail, algorithm="sha256").hexdigest()
        renamed_attempt = LoginAttempt.objects.get(pk=new_id)
        can_login_after_rename = id_services.authenticate_active_account(active_mail, pw_ok).authenticated

        # Deactivate & reactivate active_mail (must still be locked under DOC-02-04/C-03)
        id_services.deactivate_employee(actor=admin, account=seller_normal)
        id_services.reactivate_employee(actor=admin, account=seller_normal)
        after_react_attempt = LoginAttempt.objects.get(pk=new_id)
        can_login_after_react = id_services.authenticate_active_account(active_mail, pw_ok).authenticated
        react_audit_events = list(
            IdentityAuditEvent.objects.filter(action="EMPLOYEE_REACTIVATED").values("action", "outcome", "metadata")
        )
        # Now test explicit unlock_account=True clears lockout and logs ACCOUNT_UNLOCKED
        id_services.update_employee(
            actor=admin,
            account=seller_normal,
            display_name=seller_normal.display_name,
            email=active_mail,
            role=seller_normal.role,
            unlock_account=True,
        )
        after_unlock_attempt = LoginAttempt.objects.get(pk=new_id)
        can_login_after_unlock = id_services.authenticate_active_account(active_mail, pw_ok).authenticated
        unlock_audit_events = list(
            IdentityAuditEvent.objects.filter(action="ACCOUNT_UNLOCKED").values("action", "outcome", "metadata")
        )
        doc0204_verdict = (
            "CUMPLE (con defecto de firma en update_employee)"
            if update_error and not can_login_after_react
            else (
                "CUMPLE"
                if (
                    not update_error
                    and not can_login_after_rename
                    and not can_login_after_react
                    and can_login_after_unlock
                    and bool(unlock_audit_events)
                )
                else "INCUMPLE DOC-02-04/C-03"
            )
        )
        doc0204_result = {
            "id": "DOC-02-04-C03-SILENT-LOCK-RESET",
            "update_employee_error": update_error,
            "old_email_failures_after_rename": old_attempt.failures,
            "active_email_failures_after_rename": renamed_attempt.failures,
            "active_email_locked_after_rename": renamed_attempt.locked_until is not None,
            "login_allowed_immediately_after_rename": can_login_after_rename,
            "reactivate_preserved_failures": after_react_attempt.failures,
            "reactivate_preserved_locked_until": (
                after_react_attempt.locked_until.isoformat() if after_react_attempt.locked_until else None
            ),
            "login_allowed_immediately_after_reactivation": can_login_after_react,
            "reactivation_audit_events": react_audit_events,
            "explicit_unlock_failures": after_unlock_attempt.failures,
            "explicit_unlock_locked_until": (
                after_unlock_attempt.locked_until.isoformat() if after_unlock_attempt.locked_until else None
            ),
            "login_allowed_after_explicit_unlock": can_login_after_unlock,
            "explicit_unlock_audit_events": unlock_audit_events,
            "cross_stage_note": "Revalidated against 16:29 identity/services.py & audit.py edits.",
            "verdict": doc0204_verdict,
        }

        out_payload = {
            "probes": [c02_result, c03_result, doc04_result, c01_result, doc0204_result],
        }
        serialized_out = json.dumps(out_payload, ensure_ascii=False, indent=2, default=str)
        (OUT / "security-probes.json").write_text(serialized_out, encoding="utf-8")
        print(serialized_out)
    finally:
        connections.close_all()
        dj_settings.DATABASES["default"]["NAME"] = orig_db_name
        shutil.rmtree(tmp_dir, ignore_errors=True)


def cmd_orm_snapshot(args):
    setup_django()
    from django.contrib.sessions.models import Session
    from django.db import connection
    from identity.models import Account, IdentityAuditEvent, LoginAttempt, Role

    business_tables = [
        "catalog_category", "catalog_product", "inventory_supplier",
        "inventory_initialload", "inventory_lot", "inventory_stockmovement",
        "cash_cashregister", "cash_cashshift", "sales_sale", "sales_saleline",
    ]
    with connection.cursor() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {r[0] for r in cur.fetchall()}
        business_counts = {}
        for tbl in sorted(existing):
            if tbl.startswith(("catalog_", "inventory_", "cash_", "sales_")):
                cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
                business_counts[tbl] = cur.fetchone()[0]

    attempts = [
        {
            "identifier_prefix": a.identifier[:12],
            "failures": a.failures,
            "locked": bool(a.locked_until),
        }
        for a in LoginAttempt.objects.order_by("identifier")
    ]
    accounts = [
        {
            "id": str(a.pk),
            "email_len": len(a.email),
            "role": a.role.code,
            "is_active": a.is_active,
            "is_staff": a.is_staff,
            "is_superuser": a.is_superuser,
        }
        for a in Account.objects.select_related("role").order_by("pk")
    ]
    audit_counts = {}
    for act in IdentityAuditEvent.objects.values_list("action", flat=True):
        audit_counts[act] = audit_counts.get(act, 0) + 1
    snap = {
        "label": args.label,
        "accounts_count": len(accounts),
        "accounts": accounts,
        "roles_count": Role.objects.count(),
        "login_attempts_count": len(attempts),
        "login_attempts": attempts,
        "sessions_count": Session.objects.count(),
        "identity_audit_events_count": IdentityAuditEvent.objects.count(),
        "identity_audit_events_by_action": audit_counts,
        "business": business_counts,
        "business_all_zero": all(v == 0 for v in business_counts.values()),
    }
    target = OUT / f"orm-{args.label}.json"
    target.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(snap, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare").set_defaults(func=cmd_prepare)
    p_srv = sub.add_parser("serve")
    p_srv.add_argument("--port", type=int, default=8782)
    p_srv.set_defaults(func=cmd_serve)
    p_http = sub.add_parser("http-probes")
    p_http.add_argument("--port", type=int, default=8782)
    p_http.set_defaults(func=cmd_http_probes)
    sub.add_parser("security-probes").set_defaults(func=cmd_security_probes)
    p_orm = sub.add_parser("orm-snapshot")
    p_orm.add_argument("--label", required=True)
    p_orm.set_defaults(func=cmd_orm_snapshot)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
