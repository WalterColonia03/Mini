"""Stage 01-K isolated runner: prepare, serve (StaticFilesHandler or raw WSGI), HTTP probes and ORM snapshots for local demo."""
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
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-K-20261115"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-K-20261115"
CRED_FILE = DATA / ".credentials.json"
KEY_PATH = DATA / ".django-key"

sys.path.insert(0, str(R1))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01k_settings"


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
        challenge = environ.get("HTTP_X_AUDIT01K_CHALLENGE")

        def custom_start(status, headers, exc_info=None):
            if challenge:
                proof = hmac.new(secret_bytes, challenge.encode("utf-8"), hashlib.sha256).hexdigest()
                headers = list(headers) + [("X-Audit01k-Proof", proof)]
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
    if actual_db != expected_db or DATA.resolve().name != "01-K-20261115":
        raise RuntimeError("Refusing to prepare a database outside 01-K")
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
            "admin": ("admin.01h@ejemplo.invalid", Role.Code.ADMIN, "Admin 01K", True, False, False),
            "warehouse": ("almacen.01h@ejemplo.invalid", Role.Code.WAREHOUSE, "Almacenero 01K", True, False, False),
            "seller": ("vendedor.01h@ejemplo.invalid", Role.Code.SELLER, "Vendedor 01K", True, False, False),
            "inactive": ("inactiva.01h@ejemplo.invalid", Role.Code.SELLER, "Inactiva 01K", False, False, False),
            "email254": (email_254, Role.Code.WAREHOUSE, "Boundary 254 01K", True, False, False),
            "staff_admin": ("staff.admin.01h@ejemplo.invalid", Role.Code.ADMIN, "Staff Sin Permisos 01K", True, True, False),
            "super_seller": ("super.vendedor.01h@ejemplo.invalid", Role.Code.SELLER, "Superuser Vendedor 01K", True, True, True),
            "http_admin": ("http.admin.01h@ejemplo.invalid", Role.Code.ADMIN, "HTTP Admin 01K", True, False, False),
            "http_seller": ("http.vendedor.01h@ejemplo.invalid", Role.Code.SELLER, "HTTP Seller 01K", True, False, False),
            "http_deact": ("http.deact.01h@ejemplo.invalid", Role.Code.SELLER, "HTTP Deact 01K", True, False, False),
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
    st_root, hdr_root, _, html_root = _raw_http(port, "GET", "/", headers={"X-Audit01k-Challenge": nonce})
    expected_proof = hmac.new(KEY_PATH.read_text(encoding="utf-8").strip().encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    assert st_root == 200 and hdr_root.get("x-audit01k-proof") == expected_proof, "Failed raw WSGI server proof"

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
    st, hdrs, _, _ = _raw_http(port, "GET", "/", headers={"X-Audit01k-Challenge": nonce})
    expected_proof = hmac.new(KEY_PATH.read_text(encoding="utf-8").strip().encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    assert st == 200 and hdrs.get("x-audit01k-proof") == expected_proof, "Failed server proof"
    results.append({
        "id": "HTTP-01-KET-ROOT",
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
    p_srv.add_argument("--port", type=int, default=8800)
    p_srv.add_argument("--no-static", action="store_true")
    p_srv.set_defaults(func=cmd_serve)
    p_raw = sub.add_parser("raw-wsgi-probes")
    p_raw.add_argument("--port", type=int, default=8800)
    p_raw.set_defaults(func=cmd_raw_wsgi_probes)
    p_http = sub.add_parser("http-probes")
    p_http.add_argument("--port", type=int, default=8800)
    p_http.set_defaults(func=cmd_http_probes)
    p_orm = sub.add_parser("orm-snapshot")
    p_orm.add_argument("--label", required=True)
    p_orm.set_defaults(func=cmd_orm_snapshot)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
