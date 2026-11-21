"""Revalidate AUTH03 in real Chrome against a new exclusive SQLite database.

Usage: r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/soporte/audit02a_run.py run
Every run is preserved. No reset, flush, deletion, production .env or database access.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal

SUPPORT = Path(__file__).resolve().parent
RESULTS = SUPPORT.parent
ROOT = RESULTS.parent.parent
APP = ROOT / "r1-pmv"
sys.path[:0] = [str(APP), str(SUPPORT)]

def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def setup():
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit02a_settings"
    import django
    django.setup()

def snapshot():
    from cash.models import CashShift, CashShiftClose
    from sales.models import SaleDraft, Sale, SaleLine
    from inventory.models import Lot
    from identity.models import Account
    from django.contrib.sessions.models import Session
    return {
        "shifts": list(CashShift.objects.order_by("id").values("id", "seller__email", "status", "opening_amount")),
        "closes": list(CashShiftClose.objects.order_by("id").values("cash_shift_id", "counted_amount", "expected_amount")),
        "drafts": [{"id": str(d.pk), "seller": d.seller.email, "status": d.status,
                    "discarded_at": d.discarded_at,
                    "lines": list(d.lines.order_by("id").values("id", "product_id", "quantity", "unit_price"))}
                   for d in SaleDraft.objects.select_related("seller").order_by("id")],
        "lots": list(Lot.objects.order_by("id").values("id", "available_quantity")),
        "sales_count": Sale.objects.count(), "sale_lines_count": SaleLine.objects.count(),
        "sessions_by_user": {a.email: sum(s.get_decoded().get("_auth_user_id") == str(a.pk)
                                         for s in Session.objects.all()) for a in Account.objects.all()},
    }

def prepare(run):
    from django.core.management import call_command
    from identity.models import Account, Role
    from cash.models import CashRegister
    from catalog.models import Category, Product
    from inventory.models import InitialInventoryLoad, Lot
    call_command("migrate", verbosity=0, interactive=False)
    creds = {}
    actors = {}
    for alias, code, label in [("admin", "ADMIN", "AUD02A Administrador"),
                                ("warehouse", "ALMACENERO", "AUD02A Almacenero"),
                                ("seller", "VENDEDOR", "AUD02A Vendedor Uno"),
                                ("seller2", "VENDEDOR", "AUD02A Vendedor Dos")]:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": {"ADMIN":"Administrador", "ALMACENERO":"Almacenero", "VENDEDOR":"Vendedor"}[code]})
        pwd = "Aa1!" + secrets.token_urlsafe(18)
        account = Account.objects.create_user(alias + "@audit02a.invalid", pwd, display_name=label, role=role)
        creds[alias] = {"email": account.email, "password": pwd}
        actors[alias] = account
    CashRegister.objects.get_or_create(code="CAJA-01")
    category = Category.objects.create(name="AUD02A Prueba aislada")
    product = Product.objects.create(category=category, name="AUD02A Producto", barcode="775000000202", sale_price=Decimal("8.50"))
    load = InitialInventoryLoad.objects.create(product=product, responsible=actors["warehouse"])
    Lot.objects.create(product=product, initial_load=load, number="AUD02A-LOTE", initial_quantity=20,
                       available_quantity=20, unit_cost=Decimal("5.00"), expiration_date=datetime.now(timezone.utc).date()+timedelta(days=30))
    write(run / ".credentials.json", creds)
    write(run / "fixture.json", {"product_id": str(product.pk), "seller_id": str(actors["seller"].pk),
                                 "users": {k: v["email"] for k,v in creds.items()}, "initial": snapshot()})

def main():
    action = sys.argv[1]
    if action in ("snapshot", "serve"):
        setup()
        if action == "snapshot":
            print(json.dumps(snapshot(), default=str, ensure_ascii=False))
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(["manage.py", "runserver", "127.0.0.1:"+os.environ["AUDIT02A_PORT"], "--noreload", "--insecure"])
        return
    if action != "run":
        raise SystemExit("Expected run, snapshot or serve")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run = RESULTS / "datos" / ("etapa02a-"+stamp)
    evidence = RESULTS / "evidencias" / ("02-A-"+stamp)
    protected = [APP / "r1_pmv.sqlite3", *(RESULTS / "datos").rglob("*.sqlite3")]
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    run.mkdir(exist_ok=False)
    evidence.mkdir(exist_ok=False)
    write(run / "marker.json", {"run": run.name, "created_utc": stamp})
    (run / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    write(evidence / "baseline.json", {"protected_databases": before,
          "source_sha256": {str(p.relative_to(ROOT)): digest(p) for mod in ["identity", "cash", "sales"]
                            for p in (APP / mod).rglob("*") if p.suffix in (".py", ".html")},
          "git_status": subprocess.check_output(["git", "status", "--short"], cwd=APP, text=True)})
    os.environ.update(AUDIT02A_RUN_DIR=str(run), AUDIT02A_EVIDENCE=str(evidence), AUDIT02A_PYTHON=sys.executable)
    setup()
    prepare(run)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    os.environ["AUDIT02A_PORT"] = str(port)
    server = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = {"run": run.name, "evidence": str(evidence.relative_to(ROOT)), "port": port}
    try:
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            if server.poll() is not None:
                raise RuntimeError("Isolated server failed to start")
            time.sleep(.1)
        browser = subprocess.run(["node", str(SUPPORT / "audit02a_chrome.cjs")], capture_output=True, text=True, encoding="utf-8")
        # Browser output contains only IDs/counts; no HTML, cookies or form secrets.
        result.update(browser_exit=browser.returncode, browser_output=browser.stdout, browser_error=browser.stderr)
        write(evidence / "orm-final.json", snapshot())
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        # The Windows venv launcher may exit just before its server socket closes.
        # Observe closure for up to five seconds instead of assuming it is instant.
        result["port_closed"] = False
        for _ in range(50):
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) != 0:
                    result["port_closed"] = True
                    break
            time.sleep(.1)
        result["protected_unchanged"] = {str(p.relative_to(ROOT)): digest(p) == before[str(p.relative_to(ROOT))] for p in protected}
        result["final_database_sha256"] = digest(run / "audit.sqlite3")
        write(evidence / "closure.json", result)
    print(json.dumps(result, indent=2))
    if result.get("browser_exit") != 0 or not result["port_closed"] or not all(result["protected_unchanged"].values()):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
