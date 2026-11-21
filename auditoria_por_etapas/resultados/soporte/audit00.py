"""Reproducible stage-00 bootstrap and bounded checks. No destructive seed."""
from __future__ import annotations
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
sys.path.insert(0, str(APP))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit_settings"
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connection

DATA = Path(settings.DATABASES["default"]["NAME"]).parent
EVIDENCE = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias"
EVIDENCE.mkdir(parents=True, exist_ok=True)
assert Path(connection.settings_dict["NAME"]).resolve() == DATA / "audit.sqlite3"
assert DATA.is_relative_to(ROOT / "auditoria_por_etapas" / "resultados" / "datos")

def output(name, value):
    path = EVIDENCE / name
    serialized = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != serialized:
            stamp = datetime.now(ZoneInfo("America/Lima")).strftime("%Y%m%d-%H%M%S-%f")
            repeat_dir = EVIDENCE / "repeticiones"
            repeat_dir.mkdir(exist_ok=True)
            path = repeat_dir / f"{stamp}-{name}"
            with path.open("x", encoding="utf-8") as handle:
                handle.write(serialized)
    print(f"Evidencia: {path.relative_to(EVIDENCE)}")
    print(json.dumps(value, ensure_ascii=False, default=str))

def baseline():
    original = APP / "r1_pmv.sqlite3"
    return {"file": "r1-pmv/r1_pmv.sqlite3", "size": original.stat().st_size,
            "sha256": hashlib.sha256(original.read_bytes()).hexdigest()}

command = sys.argv[1] if len(sys.argv) > 1 else "inspect"
if command == "prepare":
    # Refuse to reseed existing accounts/database; preserve prior audit sessions.
    if (DATA / "prepared.json").exists():
        raise SystemExit("Already prepared; use inspect/serve. No data was reset.")
    if (DATA / "audit.sqlite3").exists():
        raise SystemExit("Unmarked audit database exists; refusing migration or seed. Inspect it manually.")
    before = baseline()
    call_command("migrate", interactive=False, verbosity=1)
    from identity.models import Role, Account
    from catalog.models import Category
    password = os.environ.get("AUDIT_PASSWORD") or getpass.getpass("Temporary audit password: ")
    for code, label, email in [
        (Role.Code.ADMIN, "Administrador", "admin.audit00@example.invalid"),
        (Role.Code.WAREHOUSE, "Almacenero", "almacen.audit00@example.invalid"),
        (Role.Code.SELLER, "Vendedor", "vendedor.audit00@example.invalid"),
    ]:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": label})
        Account.objects.create_user(email=email, password=password, role=role,
                                    display_name=f"AUD00 {label}", is_staff=False)
    Category.objects.create(name="AUD00 Enlatados ficticios")
    summary = {"database": str(DATA / "audit.sqlite3"), "accounts": 3,
               "categories": 1, "products": 0, "original_before": before,
               "original_after": baseline(), "reset_existing_data": False}
    (DATA / "prepared.json").write_text(json.dumps(summary), encoding="utf-8")
    output("00-preparacion.json", summary)
elif command == "check":
    call_command("check")
    call_command("makemigrations", check=True, dry_run=True, verbosity=1)
elif command == "serve":
    call_command("runserver", "127.0.0.1:8765", use_reloader=False, insecure_serving=True)
elif command == "inspect":
    from identity.models import Account
    from catalog.models import Category, Product
    from inventory.models import Lot
    from cash.models import CashShift
    from sales.models import Sale
    output("00-persistencia.json", {"database": str(DATA / "audit.sqlite3"),
        "accounts": Account.objects.count(), "categories": Category.objects.count(),
        "products": [{"name": p.name, "barcode": p.barcode, "sale_price": str(p.sale_price),
                      "minimum_stock": p.minimum_stock, "physical_stock": p.physical_stock,
                      "sellable_stock": p.sellable_stock, "is_sellable": p.is_sellable}
                     for p in Product.objects.all()],
        "lots": Lot.objects.count(), "turns": CashShift.objects.count(), "sales": Sale.objects.count(),
        "original_current": baseline(),
        "original_unchanged": baseline() == json.loads((DATA / "prepared.json").read_text())["original_before"]})
elif command == "routes":
    from django.urls import URLPattern, URLResolver, get_resolver
    rows = []
    def walk(patterns, prefix="", namespace=""):
        for entry in patterns:
            path = prefix + str(entry.pattern)
            if isinstance(entry, URLResolver):
                walk(entry.url_patterns, path, namespace + ((entry.namespace + ":") if entry.namespace else ""))
            elif isinstance(entry, URLPattern):
                callback = entry.callback
                rows.append({"route": "/" + path, "name": namespace + (entry.name or ""),
                             "callback": callback.__module__ + "." + callback.__name__,
                             "execution": "NO EJECUTADO (inventario de resolver)"})
    walk(get_resolver().url_patterns)
    output("00-rutas-resueltas.json", rows)
elif command == "set-password":
    from identity.models import Account
    password = getpass.getpass("New password for the three AUD00 fixtures only: ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters. Nothing changed.")
    from django.db import transaction
    with transaction.atomic():
        for email in ("admin.audit00@example.invalid", "almacen.audit00@example.invalid", "vendedor.audit00@example.invalid"):
            account = Account.objects.get(email=email, display_name__startswith="AUD00 ")
            account.set_password(password)
            account.save(update_fields=["password"])
    print("Updated only the three isolated AUD00 fixture accounts. No password logged.")
elif command == "http":
    import hmac
    import http.cookiejar
    import secrets
    import urllib.error
    import urllib.parse
    import urllib.request
    from catalog.models import Category, Product
    from inventory.models import Lot
    from cash.models import CashShift
    from sales.models import Sale
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    def business_state():
        return {"products": list(Product.objects.order_by("id").values("id", "name", "barcode", "sale_price", "minimum_stock")),
                "lots": Lot.objects.count(), "shifts": CashShift.objects.count(), "sales": Sale.objects.count()}
    before = business_state()
    results = []
    base = "http://127.0.0.1:8765"
    # A listening port is not evidence that it belongs to this isolated server.
    # Authenticate it before requesting the password, logging in or posting data.
    challenge = secrets.token_hex(32)
    request_identity = urllib.request.Request(base + "/", headers={"X-Audit00-Challenge": challenge})
    expected_proof = hmac.new(settings.SECRET_KEY.encode("utf-8"), challenge.encode("ascii"), hashlib.sha256).hexdigest()
    try:
        with urllib.request.urlopen(request_identity, timeout=10) as response:
            proof = response.headers.get("X-Audit00-Proof", "")
    except (urllib.error.URLError, OSError) as exc:
        raise SystemExit("Cannot verify isolated server; no credentials or POST sent.") from exc
    if not hmac.compare_digest(proof, expected_proof):
        raise SystemExit("Server is not the authenticated isolated audit instance; no credentials or POST sent.")
    password = os.environ.get("AUDIT_PASSWORD") or getpass.getpass("Existing AUD00 fixture password: ")
    def record(case, expected, observed):
        results.append({"case": case, "expected": expected, "observed": observed, "passed": expected == observed})
    for role, email in [("VISITANTE", None), ("ADMIN", "admin.audit00@example.invalid"),
                        ("ALMACENERO", "almacen.audit00@example.invalid"),
                        ("VENDEDOR", "vendedor.audit00@example.invalid")]:
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect())
        def request(path, data=None):
            payload = urllib.parse.urlencode(data).encode() if data is not None else None
            req = urllib.request.Request(base + path, data=payload, headers={"Referer": base + "/"})
            try:
                response = opener.open(req, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            return response.code, response.headers.get("Location"), response.read().decode("utf-8")
        def csrf():
            return next(cookie.value for cookie in jar if cookie.name == "audit00_csrftoken")
        status, _, _ = request("/")
        record(role + ": GET login", 200, status)
        if email:
            status, location, _ = request("/", {"email": email, "password": password, "csrfmiddlewaretoken": csrf()})
            record(role + ": login real HTTP + CSRF", [302, "/inicio/"], [status, location])
            if status != 302:
                raise SystemExit("Audit login failed; stopped before further requests.")
        status, location, body = request("/productos/")
        expected = 302 if role == "VISITANTE" else (403 if role == "VENDEDOR" else 200)
        record(role + ": GET catalogo", expected, status)
        if role == "VISITANTE":
            record(role + ": redireccion protegida", "/?next=/productos/", location)
        if role in {"ADMIN", "ALMACENERO"}:
            record(role + ": producto creado por UI visible", True, "AUD00 Atún ficticio" in body)
        if role != "ADMIN":
            status, _, _ = request("/productos/nuevo/")
            record(role + ": GET alta", 302 if role == "VISITANTE" else 403, status)
            status, _, _ = request("/productos/nuevo/", {
                "csrfmiddlewaretoken": csrf(), "name": "AUD00 Prohibido " + role,
                "barcode": "AUD00-DENIED-" + role,
                "category": str(Category.objects.get(name="AUD00 Enlatados ficticios").pk),
                "unit": "UND", "sale_price": "6.50", "minimum_stock": "10"})
            record(role + ": POST alta valido con CSRF", 302 if role == "VISITANTE" else 403, status)
        if email:
            status, location, _ = request("/salir/", {"csrfmiddlewaretoken": csrf()})
            record(role + ": logout HTTP", [302, "/"], [status, location])
    after = business_state()
    record("Rechazos no alteran productos/lotes/turnos/ventas", before, after)
    record("Base original conserva SHA256", json.loads((DATA / "prepared.json").read_text())["original_before"], baseline())
    result = {"timestamp": datetime.now(ZoneInfo("America/Lima")).isoformat(),
              "tool": "Python urllib + HTTP real; no Django test client", "base": base,
              "database": str(DATA / "audit.sqlite3"), "cases": results,
              "passed": sum(r["passed"] for r in results), "total": len(results),
              "scope": "Bootstrap y permisos de catalogo; no auditoria completa de HU ni suite del proyecto"}
    output("20261109-08-http.json", result)
    if not all(r["passed"] for r in results):
        raise SystemExit(1)
else:
    raise SystemExit("Use prepare, check, serve, inspect, routes, set-password or http")
