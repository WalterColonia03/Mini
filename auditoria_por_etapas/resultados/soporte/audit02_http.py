"""Verificación HTTP + ORM contra el servidor aislado vivo de la Etapa 02."""

from __future__ import annotations

import http.cookiejar
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from decimal import Decimal
from pathlib import Path


SOPORTE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = SOPORTE_DIR.parent
REPO_ROOT = RESULTADOS_DIR.parent.parent
APP_ROOT = REPO_ROOT / "r1-pmv"
EVIDENCIAS_DIR = RESULTADOS_DIR / "evidencias"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(SOPORTE_DIR) not in sys.path:
    sys.path.insert(0, str(SOPORTE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "audit02_settings")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpSession:
    def __init__(self, base_url: str = "http://127.0.0.1:8767") -> None:
        self.base_url = base_url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar),
            NoRedirectHandler(),
        )

    def request(
        self,
        method: str,
        path: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        url = f"{self.base_url}{path}"
        req_headers = {"Referer": f"{self.base_url}/"}
        if headers:
            req_headers.update(headers)
        encoded = None
        if data is not None:
            encoded = urllib.parse.urlencode(data).encode("utf-8")
            req_headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=encoded, headers=req_headers, method=method)
        try:
            with self.opener.open(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return {
                    "status": resp.status,
                    "location": resp.headers.get("Location"),
                    "cache_control": resp.headers.get("Cache-Control"),
                    "stage": resp.headers.get("X-Audit02-Stage"),
                    "proof": resp.headers.get("X-Audit02-Proof"),
                    "body": body,
                }
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            return {
                "status": err.code,
                "location": err.headers.get("Location"),
                "cache_control": err.headers.get("Cache-Control"),
                "stage": err.headers.get("X-Audit02-Stage"),
                "proof": err.headers.get("X-Audit02-Proof"),
                "body": body,
            }

    def csrf_token(self, html: str) -> str:
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
        if not match:
            raise RuntimeError("No se encontró csrfmiddlewaretoken en el HTML.")
        return match.group(1)

    def login(self, email: str, password: str) -> dict[str, object]:
        get_res = self.request("GET", "/")
        token = self.csrf_token(str(get_res["body"]))
        return self.request(
            "POST",
            "/",
            {"csrfmiddlewaretoken": token, "email": email, "password": password},
        )


def main() -> int:
    import django

    django.setup()
    from cash.models import CashShift
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Product
    from django.contrib.sessions.models import Session
    from identity.models import Account, Role
    from inventory.models import Lot
    from sales.models import SaleDraft
    from sales.services import add_product_to_draft

    checks: list[dict[str, object]] = []

    def record(check_id: str, ok: bool, details: dict[str, object]) -> None:
        checks.append({"id": check_id, "ok": bool(ok), "details": details})
        if not ok:
            raise AssertionError(f"Check {check_id} falló: {details}")

    # 1. Prueba de proceso vivo con nonce único
    probe = HttpSession()
    nonce = f"http-check-{int(datetime.now().timestamp())}"
    res_probe = probe.request("GET", "/", headers={"X-Audit02-Challenge": nonce})
    record(
        "PROOF-LIVE-SERVER",
        res_probe["status"] == 200 and res_probe["proof"] == f"ETAPA-02:{nonce}:audit.sqlite3",
        {
            "status": res_probe["status"],
            "proof": res_probe["proof"],
            "cache_control": res_probe["cache_control"],
        },
    )

    # 2. Sublote 02-A: HU-AUTH-03 (con turno abierto y borrador con líneas)
    seller1 = Account.objects.get(email_normalized="ventas@minimarket.local")
    seller2 = Account.objects.get(email_normalized="ventas2@minimarket.local")
    product = Product.objects.get(barcode="775000000201")
    lot = Lot.objects.get(number="LOT-AUD02-01")

    CashShift.objects.filter(status=CashShift.Status.OPEN).update(status=CashShift.Status.CLOSED)
    SaleDraft.objects.filter(status=SaleDraft.Status.ACTIVE).update(status=SaleDraft.Status.DISCARDED)

    shift = open_cash_shift(actor=seller1, opening_amount=Decimal("60.00"))
    s1_http = HttpSession()
    r_login_s1 = s1_http.login("ventas@minimarket.local", "Audit02!Ven")
    r_salir_no_draft = s1_http.request("GET", "/salir/")
    record(
        "HU-AUTH-03-CA01-GET-NO-DRAFT",
        r_login_s1["status"] == 302
        and r_salir_no_draft["status"] == 200
        and "Cualquier venta en preparación abierta se descartará al confirmar" in str(r_salir_no_draft["body"]),
        {
            "login_status": r_login_s1["status"],
            "salir_status": r_salir_no_draft["status"],
            "cache_control": r_salir_no_draft["cache_control"],
        },
    )

    add_product_to_draft(actor=seller1, product_id=product.pk, quantity=2)
    r_salir_with_draft = s1_http.request("GET", "/salir/")
    csrf_salir = s1_http.csrf_token(str(r_salir_with_draft["body"]))
    record(
        "HU-AUTH-03-CA02-GET-WITH-DRAFT",
        r_salir_with_draft["status"] == 200
        and "La venta en preparación se descartará. El turno abierto seguirá ligado a tu cuenta."
        in str(r_salir_with_draft["body"]),
        {
            "salir_status": r_salir_with_draft["status"],
            "active_drafts_before_post": SaleDraft.objects.filter(
                seller=seller1, status=SaleDraft.Status.ACTIVE
            ).count(),
        },
    )

    r_post_salir = s1_http.request("POST", "/salir/", {"csrfmiddlewaretoken": csrf_salir})
    lot.refresh_from_db()
    shift.refresh_from_db()
    r_after_logout = s1_http.request("GET", "/ventas/")
    record(
        "HU-AUTH-03-CA02-CA03-POST-LOGOUT",
        r_post_salir["status"] == 302
        and r_post_salir["location"] == "/"
        and SaleDraft.objects.filter(seller=seller1, status=SaleDraft.Status.ACTIVE).count() == 0
        and shift.status == CashShift.Status.OPEN
        and lot.available_quantity == 20
        and r_after_logout["status"] == 302,
        {
            "post_logout_status": r_post_salir["status"],
            "post_logout_location": r_post_salir["location"],
            "active_drafts_after_post": SaleDraft.objects.filter(
                seller=seller1, status=SaleDraft.Status.ACTIVE
            ).count(),
            "shift_status": shift.status,
            "lot_available_quantity": lot.available_quantity,
            "protected_route_after_logout_status": r_after_logout["status"],
        },
    )

    # Limpiamos turno abierto de seller1 para continuar con pruebas limpias
    close_cash_shift(actor=seller1, counted_amount=Decimal("60.00"))

    # 3. Sublote 02-B: HU-USR-01..05 y control de acceso por rol
    s_anon = HttpSession()
    s_seller = HttpSession()
    s_seller.login("ventas@minimarket.local", "Audit02!Ven")
    s_wh = HttpSession()
    s_wh.login("almacen@minimarket.local", "Audit02!Alm")
    s_admin = HttpSession()
    s_admin.login("admin@minimarket.local", "Audit02!Adm")

    r_anon_emp = s_anon.request("GET", "/empleados/")
    r_seller_emp = s_seller.request("GET", "/empleados/")
    r_wh_emp = s_wh.request("GET", "/empleados/")
    r_admin_emp = s_admin.request("GET", "/empleados/")
    r_admin_emp_q = s_admin.request("GET", "/empleados/?q=Carla")
    record(
        "HU-USR-01-LIST-AND-SEARCH-AND-RBAC",
        r_anon_emp["status"] == 302
        and r_seller_emp["status"] == 403
        and r_wh_emp["status"] == 403
        and r_admin_emp["status"] == 200
        and "no-store" in str(r_admin_emp["cache_control"])
        and "Carla Vendedora" in str(r_admin_emp_q["body"])
        and "Bruno Almacenero" not in str(r_admin_emp_q["body"]),
        {
            "anon_status": r_anon_emp["status"],
            "seller_status": r_seller_emp["status"],
            "warehouse_status": r_wh_emp["status"],
            "admin_status": r_admin_emp["status"],
            "admin_cache_control": r_admin_emp["cache_control"],
        },
    )

    # HU-USR-02: Crear empleado HTTP, duplicado y contraseña débil
    r_get_new = s_admin.request("GET", "/empleados/nuevo/")
    csrf_new = s_admin.csrf_token(str(r_get_new["body"]))
    seller_role = Role.objects.get(code=Role.Code.SELLER)
    r_dup = s_admin.request(
        "POST",
        "/empleados/nuevo/",
        {
            "csrfmiddlewaretoken": csrf_new,
            "display_name": "Duplicado HTTP",
            "email": "  VENTAS@MINIMARKET.LOCAL ",
            "password": "Abcdef1",
            "role": str(seller_role.pk),
        },
    )
    csrf_new2 = s_admin.csrf_token(str(r_dup["body"]))
    r_weak = s_admin.request(
        "POST",
        "/empleados/nuevo/",
        {
            "csrfmiddlewaretoken": csrf_new2,
            "display_name": "Débil HTTP",
            "email": "debil.http@minimarket.local",
            "password": "abcdef1",
            "role": str(seller_role.pk),
        },
    )
    record(
        "HU-USR-02-DUPLICATE-AND-WEAK-PASSWORD",
        r_dup["status"] == 200
        and "El correo ya está registrado." in str(r_dup["body"])
        and r_weak["status"] == 200
        and "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número."
        in str(r_weak["body"]),
        {
            "duplicate_status": r_dup["status"],
            "weak_password_status": r_weak["status"],
        },
    )

    EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = EVIDENCIAS_DIR / "02-http-checks.json"
    payload = {
        "stage": "ETAPA-02",
        "executed_at": datetime.now().isoformat(),
        "total_checks": len(checks),
        "all_passed": all(c["ok"] for c in checks),
        "checks": checks,
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
