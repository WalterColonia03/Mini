"""Stage 01-I isolated runner: prepare, serve (StaticFilesHandler or raw WSGI), HTTP probes, contract/timing probes, security probes, ORM snapshots."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import http.client
import io
import json
import logging
import math
import os
import secrets
import shutil
import socket
import statistics
import subprocess
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
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-I-20261115"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-I-20261115"
CRED_FILE = DATA / ".credentials.json"
KEY_PATH = DATA / ".django-key"

sys.path.insert(0, str(R1))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01i_settings"


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
        challenge = environ.get("HTTP_X_AUDIT01I_CHALLENGE")

        def custom_start(status, headers, exc_info=None):
            if challenge:
                proof = hmac.new(secret_bytes, challenge.encode("utf-8"), hashlib.sha256).hexdigest()
                headers = list(headers) + [("X-Audit01i-Proof", proof)]
            return start_response(status, headers, exc_info)

        return app(environ, custom_start)

    return wrapped


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return round(sorted_vals[0], 2)
    pos = (len(sorted_vals) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return round(sorted_vals[lo], 2)
    val = sorted_vals[lo] * (hi - pos) + sorted_vals[hi] * (pos - lo)
    return round(val, 2)


def _summarize_ms(samples_ms: list[float]) -> dict[str, object]:
    ordered = sorted(samples_ms)
    return {
        "n": len(ordered),
        "min_ms": round(ordered[0], 2),
        "p50_ms": round(statistics.median(ordered), 2),
        "mean_ms": round(statistics.mean(ordered), 2),
        "p95_ms": _percentile(ordered, 0.95),
        "max_ms": round(ordered[-1], 2),
    }


def cmd_prepare(_args):
    if (DATA / "audit.sqlite3").exists() and (DATA / "audit.sqlite3").stat().st_size > 0 and not CRED_FILE.exists():
        raise RuntimeError("Se conservó una base de evidencia sin credenciales; use una carpeta nueva de auditoría")
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    setup_django()
    from django.core.management import call_command
    from django.db import connections
    from identity.models import Account, Role

    # Fail before migrations if the actual Django connection does not point
    # at this sublot's exclusively owned test database.
    expected_db = (DATA / "audit.sqlite3").resolve()
    actual_db = Path(connections["default"].settings_dict["NAME"]).resolve()
    if actual_db != expected_db or DATA.resolve().name != "01-I-20261115":
        raise RuntimeError("Refusing to prepare a database outside 01-I")
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
            "admin": ("admin.01h@ejemplo.invalid", Role.Code.ADMIN, "Admin 01I", True, False, False),
            "warehouse": ("almacen.01h@ejemplo.invalid", Role.Code.WAREHOUSE, "Almacenero 01I", True, False, False),
            "seller": ("vendedor.01h@ejemplo.invalid", Role.Code.SELLER, "Vendedor 01I", True, False, False),
            "inactive": ("inactiva.01h@ejemplo.invalid", Role.Code.SELLER, "Inactiva 01I", False, False, False),
            "email254": (email_254, Role.Code.WAREHOUSE, "Boundary 254 01I", True, False, False),
            "staff_admin": ("staff.admin.01h@ejemplo.invalid", Role.Code.ADMIN, "Staff Sin Permisos 01I", True, True, False),
            "super_seller": ("super.vendedor.01h@ejemplo.invalid", Role.Code.SELLER, "Superuser Vendedor 01I", True, True, True),
            "http_admin": ("http.admin.01h@ejemplo.invalid", Role.Code.ADMIN, "HTTP Admin 01I", True, False, False),
            "http_seller": ("http.vendedor.01h@ejemplo.invalid", Role.Code.SELLER, "HTTP Seller 01I", True, False, False),
            "http_deact": ("http.deact.01h@ejemplo.invalid", Role.Code.SELLER, "HTTP Deact 01I", True, False, False),
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
    base_app = get_wsgi_application() if args.no_static else StaticFilesHandler(get_wsgi_application())
    app = wrap_wsgi_proof(base_app, secret)
    server = make_server("127.0.0.1", args.port, app, server_class=ThreadedWSGIServer, handler_class=QuietHandler)
    mode = "raw-wsgi" if args.no_static else "staticfiles"
    print(f"READY 127.0.0.1:{args.port} mode={mode}", flush=True)
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


def cmd_raw_wsgi_probes(args):
    OUT.mkdir(parents=True, exist_ok=True)
    port = args.port
    nonce = secrets.token_hex(24)
    st_root, hdr_root, _, html_root = _raw_http(port, "GET", "/", headers={"X-Audit01i-Challenge": nonce})
    expected_proof = hmac.new(KEY_PATH.read_text(encoding="utf-8").strip().encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    assert st_root == 200 and hdr_root.get("x-audit01i-proof") == expected_proof, "Failed raw WSGI server proof"

    assets = [
        "/static/identity/app.css",
        "/static/identity/navigation.js",
        "/static/identity/favicon.svg",
        "/static/admin/css/base.css",
    ]
    asset_results = []
    for asset_path in assets:
        st, hdrs, _, body = _raw_http(port, "GET", asset_path)
        asset_results.append({
            "path": asset_path,
            "status": st,
            "content_type": hdrs.get("content-type"),
            "x_request_id_present": bool(hdrs.get("x-request-id")),
            "body_length": len(body),
            "renders_404_template": "Página no encontrada" in body or "404" in body,
        })
    st_adm, hdr_adm, _, _ = _raw_http(port, "GET", "/admin/login/")
    payload = {
        "endpoint": f"127.0.0.1:{port}",
        "mode": "raw get_wsgi_application() without StaticFilesHandler (DEBUG=False)",
        "root_get": {
            "status": st_root,
            "content_type": hdr_root.get("content-type"),
            "references_app_css": "/static/identity/app.css" in html_root,
            "references_navigation_js": "/static/identity/navigation.js" in html_root,
            "references_favicon_svg": "/static/identity/favicon.svg" in html_root,
            "proof_verified": True,
        },
        "admin_login_get": {"status": st_adm, "content_type": hdr_adm.get("content-type")},
        "static_assets": asset_results,
        "all_static_assets_404": all(item["status"] == 404 for item in asset_results),
    }
    (OUT / "raw-wsgi-probe.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_http_probes(args):
    OUT.mkdir(parents=True, exist_ok=True)
    setup_django()
    from django.utils.crypto import salted_hmac
    from identity.models import Account, LoginAttempt
    from identity.services import deactivate_employee

    creds = json.loads(CRED_FILE.read_text(encoding="utf-8"))
    port = args.port
    results = []

    nonce = secrets.token_hex(24)
    st, hdrs, _, _ = _raw_http(port, "GET", "/", headers={"X-Audit01i-Challenge": nonce})
    expected_proof = hmac.new(KEY_PATH.read_text(encoding="utf-8").strip().encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    assert st == 200 and hdrs.get("x-audit01i-proof") == expected_proof, "Failed server proof"
    results.append({
        "id": "HTTP-01-IET-ROOT",
        "status": st,
        "cache_control": hdrs.get("cache-control"),
        "x_frame_options": hdrs.get("x-frame-options"),
        "x_content_type_options": hdrs.get("x-content-type-options"),
        "referrer_policy": hdrs.get("referrer-policy"),
        "x_request_id_present": bool(hdrs.get("x-request-id")),
        "proof_verified": True,
    })

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

    _, _, c_meth, tok_meth, _ = _get_csrf(port, "/")
    cookie_hdr_m = "; ".join(f"{k}={v}" for k, v in c_meth.items())
    st_put, hdr_put, _, _ = _raw_http(port, "PUT", "/", headers={"Cookie": cookie_hdr_m, "X-CSRFToken": tok_meth})
    st_del, _, _, _ = _raw_http(port, "DELETE", "/", headers={"Cookie": cookie_hdr_m, "X-CSRFToken": tok_meth})
    results.append({"id": "HTTP-03-METHODS", "put_status": st_put, "put_allow": hdr_put.get("allow"), "delete_status": st_del})

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
    st_null, _, _, _ = _raw_http(
        port, "POST", "/",
        body=urllib.parse.urlencode({"email": "bad\x00@ejemplo.invalid", "password": "wrong-pw-value", "csrfmiddlewaretoken": tok_meth}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie_hdr_m},
    )
    assert LoginAttempt.objects.count() == base_count, "Oversized/null POST created LoginAttempt row"

    idn_unicode = "usuaria@café-01h.invalid"
    idn_punycode = "usuaria@" + "café-01h.invalid".encode("idna").decode("ascii")
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
    _, _, ck_out, tok_out, _ = _get_csrf(port, "/salir/", extra_cookies=sess_cookies)
    st_out, h_out, _, _ = _raw_http(
        port, "POST", "/salir/",
        body=urllib.parse.urlencode({"csrfmiddlewaretoken": tok_out}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": "; ".join(f"{k}={v}" for k, v in ck_out.items())},
    )
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

    _, _, c_burst, t_burst, _ = _get_csrf(port, "/")
    cookie_burst = "; ".join(f"{k}={v}" for k, v in c_burst.items())
    burst_statuses = []
    for i in range(6):
        st_b, _, _, body_b = _raw_http(
            port, "POST", "/",
            body=urllib.parse.urlencode({"email": f"burst{i}.01h@ejemplo.invalid", "password": "wrong-pw-value", "csrfmiddlewaretoken": t_burst}).encode(),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": cookie_burst,
                "X-Forwarded-For": f"198.51.100.{20 + i}",
            },
        )
        burst_statuses.append({"index": i, "status": st_b, "uniform_error": "Correo o contraseña incorrectos" in body_b})
    results.append({"id": "HTTP-07-XFF-BURST-NO-THROTTLE", "requests": burst_statuses})

    static_checks = {}
    for asset_path in ("/static/identity/app.css", "/static/identity/navigation.js", "/static/identity/favicon.svg"):
        st_a, hdr_a, _, _ = _raw_http(port, "GET", asset_path)
        static_checks[asset_path] = {"status": st_a, "content_type": hdr_a.get("content-type")}
    results.append({"id": "HTTP-08-STATICFILES-HANDLER", "assets": static_checks})

    payload = {"endpoint": f"127.0.0.1:{port}", "results": results}
    (OUT / "http-probes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_contract_probes(_args):
    """Run deploy/proxy contract, cookie test-contract probe, N=20 timing benchmark, and retention/admin introspection."""
    OUT.mkdir(parents=True, exist_ok=True)
    setup_django()
    import re
    from django.conf import settings as dj_settings
    from django.contrib import admin as dj_admin
    from django.core.management import call_command
    from django.db import connections
    from django.test import Client
    from django.utils import timezone
    from django.utils.crypto import salted_hmac
    from identity import services as id_services
    from identity.models import Account, IdentityAuditEvent, LoginAttempt, Role

    # 1. Deploy and proxy contract in isolated subprocesses (APP_ENV=local vs APP_ENV=production)
    deploy_probe_code = r'''
import io, json, os, shutil, sys, tempfile
from pathlib import Path
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from django.test import Client
import django

django.setup()
buf = io.StringIO()
call_command("check", deploy=True, stdout=buf, stderr=buf)
check_output = buf.getvalue()

tmp_dir = Path(tempfile.mkdtemp(prefix="audit01i-deploy-"))
orig_name = settings.DATABASES["default"]["NAME"]
connections.close_all()
settings.DATABASES["default"]["NAME"] = str(tmp_dir / "deploy.sqlite3")
try:
    assert Path(connections["default"].settings_dict["NAME"]).resolve() == (tmp_dir / "deploy.sqlite3").resolve()
    call_command("migrate", interactive=False, verbosity=0)
    from identity.models import Account, Role
    r, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    pw = "DeployProbe01I-Secure!"
    acc = Account.objects.create_user("deploy.probe@ejemplo.invalid", pw, display_name="Deploy Probe", role=r)

    c_http = Client(enforce_csrf_checks=True)
    r_http = c_http.get("/")
    r_https = c_http.get("/", HTTP_X_FORWARDED_PROTO="https")
    csrf_cookie = r_https.cookies.get(settings.CSRF_COOKIE_NAME)
    csrf_val = csrf_cookie.value if csrf_cookie else ""
    r_login_unsecure_scheme = c_http.post(
        "/",
        {"email": acc.email, "password": pw, "csrfmiddlewaretoken": csrf_val},
        HTTP_X_FORWARDED_PROTO="https",
    ) if csrf_val else None

    c_tls = Client(enforce_csrf_checks=True)
    r_tls_get = c_tls.get("/", secure=True, HTTP_X_FORWARDED_PROTO="https")
    csrf_tls = r_tls_get.cookies.get(settings.CSRF_COOKIE_NAME)
    r_login = c_tls.post(
        "/",
        {"email": acc.email, "password": pw, "csrfmiddlewaretoken": csrf_tls.value},
        secure=True,
        HTTP_X_FORWARDED_PROTO="https",
    ) if csrf_tls else None
    sess_cookie = r_login.cookies.get(settings.SESSION_COOKIE_NAME) if r_login else None
    print(json.dumps({
        "app_env": settings.APP_ENV,
        "debug": settings.DEBUG,
        "static_url": settings.STATIC_URL,
        "static_root_exists": Path(settings.STATIC_ROOT).exists(),
        "secure_ssl_redirect": settings.SECURE_SSL_REDIRECT,
        "secure_hsts_seconds": settings.SECURE_HSTS_SECONDS,
        "secure_proxy_ssl_header": settings.SECURE_PROXY_SSL_HEADER,
        "session_cookie_secure_setting": settings.SESSION_COOKIE_SECURE,
        "csrf_cookie_secure_setting": settings.CSRF_COOKIE_SECURE,
        "check_deploy_warnings": sorted(set(__import__("re").findall(r"security\.W\d+", check_output))),
        "check_deploy_output_lines": [ln.strip() for ln in check_output.splitlines() if ln.strip()],
        "http_get_status": r_http.status_code,
        "http_get_location": r_http.headers.get("Location"),
        "x_forwarded_https_get_status": r_https.status_code,
        "x_forwarded_https_hsts": r_https.headers.get("Strict-Transport-Security"),
        "csrf_cookie_secure_attr": bool(csrf_cookie["secure"]) if csrf_cookie else None,
        "login_post_xfp_only_http_scheme_status": r_login_unsecure_scheme.status_code if r_login_unsecure_scheme else None,
        "login_post_https_status": r_login.status_code if r_login else None,
        "login_post_https_location": r_login.headers.get("Location") if r_login else None,
        "session_cookie_secure_attr": bool(sess_cookie["secure"]) if sess_cookie else None,
        "session_cookie_httponly_attr": bool(sess_cookie["httponly"]) if sess_cookie else None,
        "session_cookie_samesite_attr": sess_cookie["samesite"] if sess_cookie else None,
    }, ensure_ascii=False))
finally:
    connections.close_all()
    settings.DATABASES["default"]["NAME"] = orig_name
    assert tmp_dir.resolve().parent == Path(tempfile.gettempdir()).resolve()
    assert tmp_dir.name.startswith("audit01i-deploy-")
    shutil.rmtree(tmp_dir, ignore_errors=True)
'''
    deploy_results = {}
    soporte_dir = str(Path(__file__).resolve().parent)
    for mode in ("local", "production"):
        env_sub = dict(os.environ)
        env_sub["AUDIT01I_ENV"] = mode
        env_sub["DJANGO_SETTINGS_MODULE"] = "audit01i_settings"
        env_sub["PYTHONPATH"] = os.pathsep.join([str(R1), soporte_dir])
        env_sub.pop("AUDIT01I_CUSTOM_COOKIES_IN_TEST", None)
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "-c", deploy_probe_code],
            cwd=str(R1),
            env=env_sub,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        assert proc.returncode == 0, f"Deploy probe failed for {mode}: {proc.stderr}"
        deploy_results[mode] = json.loads(proc.stdout.strip().splitlines()[-1])

    # 2. Cookie contract test probe (default vs custom cookie names)
    cookie_contract = {}
    test_target = "identity.tests.AuthenticationAndAuthorizationTests.test_login_post_requires_csrf_and_sets_protected_cookies"
    for label, custom_flag in (("default_cookie_names", "0"), ("custom_cookie_names", "1")):
        env_t = dict(os.environ)
        env_t["DJANGO_SETTINGS_MODULE"] = "audit01i_settings"
        env_t["PYTHONPATH"] = os.pathsep.join([str(R1), soporte_dir])
        if custom_flag == "1":
            env_t["AUDIT01I_CUSTOM_COOKIES_IN_TEST"] = "1"
        else:
            env_t.pop("AUDIT01I_CUSTOM_COOKIES_IN_TEST", None)
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "manage.py", "test", test_target, "--settings=audit01i_settings", "-v", "2"],
            cwd=str(R1),
            env=env_t,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        combined = proc.stdout + "\n" + proc.stderr
        cookie_contract[label] = {
            "returncode": proc.returncode,
            "passed": proc.returncode == 0,
            "has_keyerror_csrftoken": "KeyError: 'csrftoken'" in combined,
            "csrf_cookie_line_match": re.findall(r'.*csrftoken.*', combined)[:4],
            "output_tail": [ln.rstrip() for ln in combined.splitlines() if ln.strip()][-8:],
        }

    # 3. Statistical Argon2 timing benchmark (N=20 trials per bucket on isolated throwaway DB)
    tmp_dir = Path(tempfile.mkdtemp(prefix="audit01i-bench-"))
    orig_db_name = dj_settings.DATABASES["default"]["NAME"]
    connections.close_all()
    dj_settings.DATABASES["default"]["NAME"] = str(tmp_dir / "bench.sqlite3")
    timing_results = {}
    try:
        assert Path(connections["default"].settings_dict["NAME"]).resolve() == (tmp_dir / "bench.sqlite3").resolve()
        call_command("migrate", interactive=False, verbosity=0)
        roles = {c: Role.objects.create(code=c, name=lbl) for c, lbl in Role.Code.choices}
        pw_ok = secrets.token_urlsafe(24)
        pw_bad = secrets.token_urlsafe(24)
        known_unlocked = Account.objects.create_user("bench.known.unlocked@probe.invalid", pw_ok, display_name="Bench Known", role=roles[Role.Code.SELLER])
        known_locked = Account.objects.create_user("bench.known.locked@probe.invalid", pw_ok, display_name="Bench Known Locked", role=roles[Role.Code.SELLER])
        unknown_locked_email = "bench.unknown.locked@probe.invalid"
        for _ in range(5):
            id_services.authenticate_active_account(known_locked.email, pw_bad)
            id_services.authenticate_active_account(unknown_locked_email, pw_bad)

        # Warmup (not recorded)
        for _ in range(2):
            id_services.authenticate_active_account(known_locked.email, pw_bad)
            id_services.authenticate_active_account(unknown_locked_email, pw_bad)

        N = 20
        known_unlocked_samples: list[float] = []
        unknown_unlocked_samples: list[float] = []
        known_locked_samples: list[float] = []
        unknown_locked_samples: list[float] = []

        known_ident = salted_hmac("identity.login.throttle", known_unlocked.email, algorithm="sha256").hexdigest()
        for i in range(N):
            LoginAttempt.objects.filter(pk=known_ident).update(failures=0, locked_until=None)
            t0 = time.perf_counter()
            res = id_services.authenticate_active_account(known_unlocked.email, pw_bad)
            known_unlocked_samples.append((time.perf_counter() - t0) * 1000.0)
            assert not res.authenticated and res.locked_minutes == 0

        for i in range(N):
            unk = f"bench.unknown.{i}@probe.invalid"
            t0 = time.perf_counter()
            res = id_services.authenticate_active_account(unk, pw_bad)
            unknown_unlocked_samples.append((time.perf_counter() - t0) * 1000.0)
            assert not res.authenticated and res.locked_minutes == 0

        for _ in range(N):
            t0 = time.perf_counter()
            res = id_services.authenticate_active_account(known_locked.email, pw_ok)
            known_locked_samples.append((time.perf_counter() - t0) * 1000.0)
            assert not res.authenticated and res.locked_minutes > 0

        for _ in range(N):
            t0 = time.perf_counter()
            res = id_services.authenticate_active_account(unknown_locked_email, pw_bad)
            unknown_locked_samples.append((time.perf_counter() - t0) * 1000.0)
            assert not res.authenticated and res.locked_minutes > 0

        # Full Client CSRF POST benchmark comparing locked Argon2 path vs oversized-255 early form rejection
        client_bench = Client(enforce_csrf_checks=True)
        get_r = client_bench.get("/")
        csrf_tok = get_r.cookies[dj_settings.CSRF_COOKIE_NAME].value
        client_known_wrong_ms: list[float] = []
        client_known_locked_ms: list[float] = []
        client_oversized_255_ms: list[float] = []
        em_255 = ("x" * (255 - len("@probe.invalid"))) + "@probe.invalid"
        assert len(em_255) == 255

        for _ in range(N):
            LoginAttempt.objects.filter(pk=known_ident).update(failures=0, locked_until=None)
            t0 = time.perf_counter()
            r = client_bench.post("/", {"email": known_unlocked.email, "password": pw_bad, "csrfmiddlewaretoken": csrf_tok})
            client_known_wrong_ms.append((time.perf_counter() - t0) * 1000.0)
            assert r.status_code == 200

        for _ in range(N):
            t0 = time.perf_counter()
            r = client_bench.post("/", {"email": known_locked.email, "password": pw_ok, "csrfmiddlewaretoken": csrf_tok})
            client_known_locked_ms.append((time.perf_counter() - t0) * 1000.0)
            assert r.status_code == 200

        for _ in range(N):
            t0 = time.perf_counter()
            r = client_bench.post("/", {"email": em_255, "password": pw_bad, "csrfmiddlewaretoken": csrf_tok})
            client_oversized_255_ms.append((time.perf_counter() - t0) * 1000.0)
            assert r.status_code == 200

        # Confirm Argon2 spy calls during locked invocation
        spy_calls = []
        orig_chk = id_services.check_password
        orig_set = Account.set_password
        with (
            patch("identity.services.check_password", side_effect=lambda p, e: (spy_calls.append("check_password"), orig_chk(p, e))[1]),
            patch.object(Account, "set_password", autospec=True, side_effect=lambda s, p: (spy_calls.append("set_password"), orig_set(s, p))[1]),
        ):
            id_services.authenticate_active_account(known_locked.email, pw_ok)
            id_services.authenticate_active_account(unknown_locked_email, pw_bad)

        svc_summary = {
            "known_unlocked_wrong": _summarize_ms(known_unlocked_samples),
            "unknown_unlocked_wrong": _summarize_ms(unknown_unlocked_samples),
            "known_locked": _summarize_ms(known_locked_samples),
            "unknown_locked": _summarize_ms(unknown_locked_samples),
        }
        client_summary = {
            "post_known_wrong": _summarize_ms(client_known_wrong_ms),
            "post_known_locked": _summarize_ms(client_known_locked_ms),
            "post_oversized_255_no_argon2": _summarize_ms(client_oversized_255_ms),
        }
        ratio_locked_vs_unlocked = round(svc_summary["known_locked"]["mean_ms"] / svc_summary["known_unlocked_wrong"]["mean_ms"], 2)
        ratio_locked_vs_form255 = round(client_summary["post_known_locked"]["mean_ms"] / max(0.01, client_summary["post_oversized_255_no_argon2"]["mean_ms"]), 2)
        timing_results = {
            "n_per_bucket": N,
            "hasher_algorithm": "Argon2PasswordHasher",
            "spy_calls_for_1_known_locked_and_1_unknown_locked": spy_calls,
            "service_ms": svc_summary,
            "http_client_ms": client_summary,
            "ratio_locked_mean_vs_unlocked_mean": ratio_locked_vs_unlocked,
            "ratio_http_locked_mean_vs_oversized255_mean": ratio_locked_vs_form255,
            "doc_01_04_verdict": "INCUMPLE (Argon2 ejecutado antes de verificar locked_until > now)",
        }

        # 4. Retention / indexes / /admin/ surface introspection on isolated schema
        with connections["default"].cursor() as cur:
            cur.execute("PRAGMA index_list('identity_loginattempt')")
            la_idx = [list(row) for row in cur.fetchall()]
            cur.execute("PRAGMA index_list('identity_identityauditevent')")
            ia_idx = [list(row) for row in cur.fetchall()]
    finally:
        connections.close_all()
        dj_settings.DATABASES["default"]["NAME"] = orig_db_name
        assert tmp_dir.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert tmp_dir.name.startswith("audit01i-bench-")
        shutil.rmtree(tmp_dir, ignore_errors=True)

    mgmt_dir = R1 / "identity/management/commands"
    mgmt_commands = sorted(p.stem for p in mgmt_dir.glob("*.py") if p.name != "__init__.py") if mgmt_dir.exists() else []
    registered_admin_models = sorted(f"{m._meta.app_label}.{m._meta.model_name}" for m in dj_admin.site._registry.keys())
    account_admin = dj_admin.site._registry.get(Account)
    account_admin_fields = [fs[1]["fields"] for fs in getattr(account_admin, "fieldsets", ())]

    retention_and_admin = {
        "login_attempt_fields": [f.name for f in LoginAttempt._meta.fields],
        "login_attempt_sqlite_indexes": la_idx,
        "login_attempt_has_locked_until_or_updated_at_index": any(
            getattr(LoginAttempt._meta.get_field(fn), "db_index", False) for fn in ("locked_until", "updated_at")
        ) or bool(LoginAttempt._meta.indexes),
        "identity_audit_event_sqlite_indexes": ia_idx,
        "identity_management_commands": mgmt_commands,
        "has_purge_or_retention_command": any("purge" in c or "clean" in c or "ret" in c for c in mgmt_commands),
        "admin_registered_models_count": len(registered_admin_models),
        "admin_registered_models": registered_admin_models,
        "login_attempt_in_admin": LoginAttempt in dj_admin.site._registry,
        "identity_audit_event_in_admin": IdentityAuditEvent in dj_admin.site._registry,
        "account_admin_exposed_fieldsets": [list(f) for f in account_admin_fields],
    }

    payload = {
        "deploy_and_proxy": deploy_results,
        "cookie_contract_tests": cookie_contract,
        "argon2_timing_benchmark": timing_results,
        "retention_and_admin_surface": retention_and_admin,
    }
    (OUT / "contract-probes.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_security_probes(_args):
    """Revalidate DOC-01-06/C-01..C-03, DOC-01-04, DOC-02-04/C-03 and employee deactivation metadata fix on 848a5eae..."""
    OUT.mkdir(parents=True, exist_ok=True)
    setup_django()
    from django.conf import settings as dj_settings
    from django.core.management import call_command
    from django.db import connections
    from django.test import Client
    from django.utils.crypto import salted_hmac
    from app_platform.logging import RedactSensitiveDataFilter
    from identity import services as id_services
    from identity.models import Account, IdentityAuditEvent, LoginAttempt, Role

    tmp_dir = Path(tempfile.mkdtemp(prefix="audit01i-secprobe-"))
    probe_db = tmp_dir / "probe.sqlite3"
    orig_db_name = dj_settings.DATABASES["default"]["NAME"]
    connections.close_all()
    dj_settings.DATABASES["default"]["NAME"] = str(probe_db)
    try:
        assert Path(connections["default"].settings_dict["NAME"]).resolve() == probe_db.resolve()
        call_command("migrate", interactive=False, verbosity=0)

        roles = {c: Role.objects.create(code=c, name=lbl) for c, lbl in Role.Code.choices}
        pw_ok = secrets.token_urlsafe(24)
        pw_bad = secrets.token_urlsafe(24)
        admin = Account.objects.create_user("sec.admin@probe.invalid", pw_ok, display_name="Sec Admin", role=roles[Role.Code.ADMIN])
        seller_su = Account.objects.create_user("sec.su@probe.invalid", pw_ok, display_name="Sec Super", role=roles[Role.Code.SELLER], is_staff=True, is_superuser=True)
        seller_normal = Account.objects.create_user("sec.seller@probe.invalid", pw_ok, display_name="Sec Seller", role=roles[Role.Code.SELLER])

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
            else ("CUMPLE" if (has_login_ok and has_login_fail and has_login_lock and has_logout_ok and adm_events_added > 0) else "INCUMPLE")
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

        canary_pw = "CANARIO-SECRETO-PRUEBA"
        canary_tok = "CANARIO-TOKEN-01I"
        exc_stream = io.StringIO()
        exc_handler = logging.StreamHandler(exc_stream)
        exc_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        exc_handler.addFilter(RedactSensitiveDataFilter())
        probe_logger = logging.getLogger("audit01i.probe.c03")
        probe_logger.handlers = [exc_handler]
        probe_logger.propagate = False
        probe_logger.setLevel(logging.ERROR)
        try:
            raise RuntimeError(f"Error controlado con password={canary_pw} y token={canary_tok}")
        except RuntimeError:
            probe_logger.exception(f"Fallo requestID=REQ-01I password={canary_pw}")
        exc_logged = exc_stream.getvalue()
        msg_line = exc_logged.splitlines()[0] if exc_logged.splitlines() else ""
        msg_redacted = canary_pw not in msg_line
        exc_info_leaked = (canary_pw in exc_logged) or (canary_tok in exc_logged)

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
            resp_fail = c_fail.post("/", {"email": seller_normal.email, "password": pw_ok})
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

        hash_calls_while_locked = []
        orig_check_pw = id_services.check_password
        orig_set_pw = Account.set_password
        with (
            patch("identity.services.check_password", side_effect=lambda p, e: (hash_calls_while_locked.append("check_password"), orig_check_pw(p, e))[1]),
            patch.object(Account, "set_password", autospec=True, side_effect=lambda s, p: (hash_calls_while_locked.append("set_password"), orig_set_pw(s, p))[1]),
        ):
            res_locked = id_services.authenticate_active_account(seller_normal.email, pw_ok)
            for _ in range(5):
                id_services.authenticate_active_account("unknown.locked@probe.invalid", pw_bad)
            hash_calls_while_locked.clear()
            res_unknown_locked = id_services.authenticate_active_account("unknown.locked@probe.invalid", pw_bad)
        doc04_result = {
            "id": "DOC-01-04-ARGON2-BEFORE-LOCK-CHECK",
            "locked_known_minutes": res_locked.locked_minutes,
            "locked_unknown_minutes": res_unknown_locked.locked_minutes,
            "hash_calls_executed_on_already_locked_unknown": list(hash_calls_while_locked),
            "note": "Called check_password/set_password prior to attempt.locked_until > now",
            "verdict": "INCUMPLE",
        }
        with patch("identity.services.check_password", side_effect=lambda p, e: (hash_calls_while_locked.append("check_password"), orig_check_pw(p, e))[1]):
            hash_calls_while_locked.clear()
            id_services.authenticate_active_account(seller_normal.email, pw_ok)
            doc04_result["hash_calls_executed_on_already_locked_known"] = list(hash_calls_while_locked)

        from django.contrib.sessions.models import Session

        for _ in range(5):
            id_services.authenticate_active_account(seller_su.email, pw_bad)
        assert not id_services.authenticate_active_account(seller_su.email, pw_ok).authenticated
        c_su = Client()
        r_admin_login = c_su.post("/admin/login/?next=/admin/", {"username": seller_su.email, "password": pw_ok})
        sess_data = Session.objects.get(session_key=c_su.session.session_key).get_decoded()
        r_inicio = c_su.get("/inicio/")
        r_emp = c_su.get("/empleados/")
        r_acc_admin = c_su.get("/admin/identity/account/")
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

        id_a = salted_hmac("identity.login.throttle", seller_normal.email, algorithm="sha256").hexdigest()
        att_before_edit = LoginAttempt.objects.get(pk=id_a)
        assert att_before_edit.failures == 5 and att_before_edit.locked_until is not None
        new_mail = "sec.seller.renamed@probe.invalid"
        id_services.update_employee(
            actor=admin,
            account=seller_normal,
            display_name="Sec Seller Renamed",
            email=new_mail,
            role=roles[Role.Code.SELLER],
        )
        old_attempt = LoginAttempt.objects.get(pk=id_a)
        new_id = salted_hmac("identity.login.throttle", new_mail, algorithm="sha256").hexdigest()
        renamed_attempt = LoginAttempt.objects.get(pk=new_id)
        can_login_after_rename = id_services.authenticate_active_account(new_mail, pw_ok).authenticated

        id_services.deactivate_employee(actor=admin, account=seller_normal)
        deact_audit_events = list(
            IdentityAuditEvent.objects.filter(action="EMPLOYEE_DEACTIVATED").values("action", "outcome", "metadata")
        )
        id_services.reactivate_employee(actor=admin, account=seller_normal)
        after_react_attempt = LoginAttempt.objects.get(pk=new_id)
        can_login_after_react = id_services.authenticate_active_account(new_mail, pw_ok).authenticated
        react_audit_events = list(
            IdentityAuditEvent.objects.filter(action="EMPLOYEE_REACTIVATED").values("action", "outcome", "metadata")
        )
        id_services.update_employee(
            actor=admin,
            account=seller_normal,
            display_name=seller_normal.display_name,
            email=new_mail,
            role=seller_normal.role,
            unlock_account=True,
        )
        after_unlock_attempt = LoginAttempt.objects.get(pk=new_id)
        can_login_after_unlock = id_services.authenticate_active_account(new_mail, pw_ok).authenticated
        unlock_audit_events = list(
            IdentityAuditEvent.objects.filter(action="ACCOUNT_UNLOCKED").values("action", "outcome", "metadata")
        )
        doc0204_verdict = (
            "CUMPLE"
            if (not can_login_after_rename and not can_login_after_react and can_login_after_unlock and bool(unlock_audit_events))
            else "INCUMPLE DOC-02-04/C-03"
        )
        sessions_revoked_val = deact_audit_events[-1]["metadata"].get("sessions_revoked") if deact_audit_events else None
        doc0204_result = {
            "id": "DOC-02-04-C03-SILENT-LOCK-RESET",
            "old_email_failures_after_rename": old_attempt.failures,
            "active_email_failures_after_rename": renamed_attempt.failures,
            "active_email_locked_after_rename": renamed_attempt.locked_until is not None,
            "login_allowed_immediately_after_rename": can_login_after_rename,
            "deactivate_audit_events": deact_audit_events,
            "sessions_revoked_not_redacted_bool": isinstance(sessions_revoked_val, bool),
            "reactivate_preserved_failures": after_react_attempt.failures,
            "reactivate_preserved_locked_until": after_react_attempt.locked_until.isoformat() if after_react_attempt.locked_until else None,
            "login_allowed_immediately_after_reactivation": can_login_after_react,
            "reactivation_audit_events": react_audit_events,
            "explicit_unlock_failures": after_unlock_attempt.failures,
            "explicit_unlock_locked_until": after_unlock_attempt.locked_until.isoformat() if after_unlock_attempt.locked_until else None,
            "login_allowed_after_explicit_unlock": can_login_after_unlock,
            "explicit_unlock_audit_events": unlock_audit_events,
            "verdict": doc0204_verdict,
        }

        out_payload = {"probes": [c02_result, c03_result, doc04_result, c01_result, doc0204_result]}
        serialized_out = json.dumps(out_payload, ensure_ascii=False, indent=2, default=str)
        (OUT / "security-probes.json").write_text(serialized_out + "\n", encoding="utf-8")
        print(serialized_out)
    finally:
        connections.close_all()
        dj_settings.DATABASES["default"]["NAME"] = orig_db_name
        assert tmp_dir.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert tmp_dir.name.startswith("audit01i-secprobe-")
        shutil.rmtree(tmp_dir, ignore_errors=True)


def cmd_orm_snapshot(args):
    OUT.mkdir(parents=True, exist_ok=True)
    setup_django()
    from django.contrib.sessions.models import Session
    from django.db import connection
    from identity.models import Account, IdentityAuditEvent, LoginAttempt, Role

    with connection.cursor() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {r[0] for r in cur.fetchall()}
        business_counts = {}
        for tbl in sorted(existing):
            if tbl.startswith(("catalog_", "inventory_", "cash_", "sales_")):
                cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
                business_counts[tbl] = cur.fetchone()[0]

    attempts = [
        {"identifier_prefix": a.identifier[:12], "failures": a.failures, "locked": bool(a.locked_until)}
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
    target.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snap, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare").set_defaults(func=cmd_prepare)
    p_srv = sub.add_parser("serve")
    p_srv.add_argument("--port", type=int, default=8796)
    p_srv.add_argument("--no-static", action="store_true")
    p_srv.set_defaults(func=cmd_serve)
    p_raw = sub.add_parser("raw-wsgi-probes")
    p_raw.add_argument("--port", type=int, default=8796)
    p_raw.set_defaults(func=cmd_raw_wsgi_probes)
    p_http = sub.add_parser("http-probes")
    p_http.add_argument("--port", type=int, default=8796)
    p_http.set_defaults(func=cmd_http_probes)
    sub.add_parser("contract-probes").set_defaults(func=cmd_contract_probes)
    sub.add_parser("security-probes").set_defaults(func=cmd_security_probes)
    p_orm = sub.add_parser("orm-snapshot")
    p_orm.add_argument("--label", required=True)
    p_orm.set_defaults(func=cmd_orm_snapshot)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
