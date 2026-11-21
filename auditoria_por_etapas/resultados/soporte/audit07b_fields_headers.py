"""Isolated protocol probes for Stage 07 HTTP headers, field boundaries, and CT-COHERENCIA-UI."""
from __future__ import annotations

import datetime
import gc
import html
import os
import json
import sys
import tempfile
import uuid
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[3]
R1_PMV = ROOT / "r1-pmv"
EVID_DIR = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias" / "07-B-20261114"

sys.path.insert(0, str(R1_PMV))

TMP_DIR = tempfile.TemporaryDirectory(prefix="audit07b_fields_", ignore_cleanup_errors=True)
DB_PATH = Path(TMP_DIR.name) / "fields_probe.sqlite3"

os.environ.update(
    APP_ENV="test",
    DATABASE_URL="sqlite",
    DJANGO_DEBUG="false",
    DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    DJANGO_SECRET_KEY="audit07b-fields-ephemeral-secret-key-not-for-prod-1234567890",
)

from config import env as config_env  # noqa: E402

config_env.load_dotenv = lambda path=None: None
from django.conf import settings as _unused_check  # noqa: E402,F401
import config.settings as base_settings  # noqa: E402
from django.conf import settings  # noqa: E402

cfg = {k: getattr(base_settings, k) for k in dir(base_settings) if k.isupper()}
cfg["DATABASES"] = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DB_PATH}}
cfg["EMAIL_BACKEND"] = "django.core.mail.backends.locmem.EmailBackend"
settings.configure(**cfg)

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import CaptureQueriesContext, setup_test_environment  # noqa: E402
from django.utils import timezone  # noqa: E402

setup_test_environment()
call_command("migrate", verbosity=0)

from catalog.models import Category, Product, ProductBarcodeKey  # noqa: E402
from catalog.services import toggle_category_status, toggle_product_availability  # noqa: E402
from identity.models import Account, Role  # noqa: E402
from inventory.models import Lot, Supplier  # noqa: E402
from inventory.services import LotInput, confirm_initial_load, register_physical_adjustment  # noqa: E402


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.alerts: list[str] = []
        self.in_alert = False
        self.cur_alert: list[str] = []
        self.title: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrd = dict(attrs)
        cls = (attrd.get("class") or "").split()
        if "alert" in cls or attrd.get("role") == "alert":
            self.in_alert = True
            self.cur_alert = []
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "div" or tag.lower() == "p":
            if self.in_alert:
                self.alerts.append(" ".join("".join(self.cur_alert).split()))
                self.in_alert = False
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_alert:
            self.cur_alert.append(data)
        if self.in_title:
            self.title.append(data)


def build_fixtures():
    call_command("flush", verbosity=0, interactive=False)
    roles = {
        c: Role.objects.get_or_create(code=c, defaults={"name": n})[0]
        for c, n in [
            (Role.Code.ADMIN, "Administrador"),
            (Role.Code.WAREHOUSE, "Almacenero"),
            (Role.Code.SELLER, "Vendedor"),
        ]
    }
    admin = Account.objects.create_user("ad@t.inv", "Pass!2026", display_name="Ad", role=roles[Role.Code.ADMIN])
    wh = Account.objects.create_user("wh@t.inv", "Pass!2026", display_name="Wh", role=roles[Role.Code.WAREHOUSE])
    seller = Account.objects.create_user("se@t.inv", "Pass!2026", display_name="Se", role=roles[Role.Code.SELLER])

    c_act = Category.objects.create(name="Bebidas")
    c_off = Category.objects.create(name="Temporal")
    sup = Supplier.objects.create(name="Prov Uno", ruc="20111111111")

    p_agua = Product.objects.create(
        name="Água Purificada", category=c_act, barcode="012345678905", barcode_type=Product.BarcodeType.GTIN,
        unit="UND", sale_price=Decimal("2.50"), minimum_stock=5, is_active=True, controls_expiration=True,
    )
    p_zero = Product.objects.create(
        name="Producto Cero Minimo", category=c_act, barcode="7750000000024",
        unit="UND", sale_price=Decimal("4.00"), minimum_stock=0, is_active=True, controls_expiration=True,
    )
    p_off = Product.objects.create(
        name="Gaseosa Inactiva", category=c_off, barcode="7750000000031",
        unit="UND", sale_price=Decimal("6.00"), minimum_stock=5, is_active=True, controls_expiration=True,
    )

    t0 = datetime.datetime(2026, 11, 10, 15, 0, tzinfo=datetime.timezone.utc)
    with patch("django.utils.timezone.now", return_value=t0):
        confirm_initial_load(
            actor=wh, product=p_agua, supplier=sup,
            lots=[
                LotInput(number="EXP-01", quantity=4, unit_cost=Decimal("1.2000"), expiration_date=datetime.date(2026, 11, 12)),
                LotInput(number="FUT-01", quantity=8, unit_cost=Decimal("1.2000"), expiration_date=datetime.date(2026, 11, 25)),
            ],
        )
        confirm_initial_load(
            actor=wh, product=p_off, supplier=sup,
            lots=[LotInput(number="OFF-EXP", quantity=2, unit_cost=Decimal("2.0000"), expiration_date=datetime.date(2026, 11, 11))],
        )
        register_physical_adjustment(
            actor=admin, product=p_agua, number="ADJ-FUT",
            expiration_date=datetime.date(2026, 11, 15), delta=3,
            reason="Conteo físico",
        )
    toggle_category_status(actor=admin, category=c_off, is_active=False, expected_version=c_off.state_version)
    lots = {lt.number: lt for lt in Lot.objects.all()}
    return admin, wh, seller, p_agua, p_zero, p_off, lots


def mk_client(user=None):
    c = Client(HTTP_HOST="localhost")
    if user:
        c.force_login(user)
    return c


def run():
    now_fixed = datetime.datetime(2026, 11, 14, 15, 0, tzinfo=datetime.timezone.utc)
    with patch("django.utils.timezone.now", return_value=now_fixed):
        admin, wh, seller, p_agua, p_zero, p_off, lots = build_fixtures()

        # 1. HTTP Headers matrix across routes & roles
        header_matrix = []
        for route in ["/productos/", "/inventario/stock/", "/productos/vencimientos/", "/inicio/"]:
            for role_name, usr in [("ANON", None), ("VENDEDOR", seller), ("ALMACENERO", wh), ("ADMIN", admin)]:
                cl = mk_client(usr)
                r = cl.get(route)
                header_matrix.append({
                    "route": route,
                    "role": role_name,
                    "status": r.status_code,
                    "cache_control": r.headers.get("Cache-Control"),
                    "vary": r.headers.get("Vary"),
                    "location": r.headers.get("Location"),
                    "x_content_type_options": r.headers.get("X-Content-Type-Options"),
                })

        # Also test HEAD / OPTIONS / POST on Stage 07 endpoints
        method_matrix = []
        cl_ad = mk_client(admin)
        for route in ["/inventario/stock/", "/productos/vencimientos/", "/productos/"]:
            for m in ["GET", "HEAD", "POST", "PUT", "OPTIONS"]:
                resp = getattr(cl_ad, m.lower())(route)
                method_matrix.append({
                    "route": route,
                    "method": m,
                    "status": resp.status_code,
                    "allow": resp.headers.get("Allow"),
                    "cache_control": resp.headers.get("Cache-Control"),
                })

        # 2. Field ?dias= boundary matrix on /productos/vencimientos/
        lot_count_before = Lot.objects.count()
        dias_cases = []
        dias_inputs = [
            ("default_omitted", None),
            ("empty_str", ""),
            ("spaces_only", "   "),
            ("spaces_around_7", "  7  "),
            ("leading_zeros_7", "00007"),
            ("all_zeros_6", "000000"),
            ("zero", "0"),
            ("plus_7", "+7"),
            ("minus_zero", "-0"),
            ("negative_1", "-1"),
            ("min_valid_1", "1"),
            ("max_valid_3650", "3650"),
            ("over_max_3651", "3651"),
            ("huge_int", "9" * 30),
            ("float_7_5", "7.5"),
            ("sci_1e2", "1e2"),
            ("arabic_5", "٥"),
            ("nul_byte", "7\x00"),
            ("sqli", "' OR 1=1 --"),
            ("xss", "<script>alert(1)</script>"),
        ]
        cl_wh = mk_client(wh)
        for name, val in dias_inputs:
            url = "/productos/vencimientos/" if val is None else "/productos/vencimientos/?" + urlencode({"dias": val})
            r = cl_wh.get(url)
            text = r.content.decode("utf-8", errors="replace")
            ext = _TextExtractor()
            ext.feed(text)
            dias_cases.append({
                "case": name,
                "raw": val,
                "status": r.status_code,
                "context_days": r.context.get("days") if r.context else None,
                "alerts": ext.alerts,
                "escaped_xss": "<script>alert(1)</script>" not in text,
            })

        # Repeated query params ?dias=7&dias=30 and ?dias=30&dias=7
        for seq_label, qs in [("rep_7_then_30", "dias=7&dias=30"), ("rep_30_then_7", "dias=30&dias=7")]:
            r = cl_wh.get(f"/productos/vencimientos/?{qs}")
            dias_cases.append({
                "case": seq_label,
                "raw": qs,
                "status": r.status_code,
                "context_days": r.context.get("days") if r.context else None,
            })

        # Empty expirations + invalid dias error combination
        Lot.objects.filter(available_quantity__gt=0).update(available_quantity=0)
        r_empty_err = cl_wh.get("/productos/vencimientos/?dias=0")
        ext_e = _TextExtractor()
        ext_e.feed(r_empty_err.content.decode("utf-8"))
        admin, wh, seller, p_agua, p_zero, p_off, lots = build_fixtures()
        cl_wh = mk_client(wh)
        cl_ad = mk_client(admin)
        lot_count_after = Lot.objects.count()

        # 3. Field ?q= boundary probes on /productos/
        prod_count_before = Product.objects.count()
        bkeys = list(ProductBarcodeKey.objects.filter(product=p_agua).values_list("reading_key", flat=True))
        secondary_key = [k for k in bkeys if k != p_agua.barcode_normalized]
        q_inputs = [
            ("omitted", None),
            ("empty", ""),
            ("spaces_only", "   "),
            ("accent_fold", "Agua"),
            ("exact_barcode_12d", "012345678905"),
            ("secondary_barcode_key", secondary_key[0] if secondary_key else "0012345678905"),
            ("nul_byte", "Agua\x00"),
            ("long_500", "A" * 500),
            ("sqli", "' OR 1=1 --"),
            ("xss", "<script>alert(1)</script>"),
        ]
        q_cases = []
        for name, val in q_inputs:
            url = "/productos/" if val is None else "/productos/?" + urlencode({"q": val})
            with CaptureQueriesContext(connection) as qctx:
                r = cl_ad.get(url)
            txt = r.content.decode("utf-8", errors="replace")
            prods = list(r.context["products"].values_list("name", flat=True)) if r.context and "products" in r.context else []
            q_cases.append({
                "case": name,
                "raw_len": len(val) if val is not None else None,
                "status": r.status_code,
                "query_count": len(qctx),
                "invalid_query": r.context.get("invalid_query") if r.context else None,
                "matched_products": prods,
                "xss_escaped": ("<script>alert(1)</script>" not in txt) and ("&lt;script&gt;alert(1)&lt;/script&gt;" in txt if name == "xss" else True),
                "cache_control": r.headers.get("Cache-Control"),
            })
        # Repeated ?q=
        r_qrep = cl_ad.get("/productos/?q=Agua&q=Cero")
        q_cases.append({
            "case": "rep_Agua_then_Cero",
            "status": r_qrep.status_code,
            "query_echo": r_qrep.context.get("query") if r_qrep.context else None,
            "matched_products": list(r_qrep.context["products"].values_list("name", flat=True)),
        })
        # Check ALMACENERO view of /productos/ hides Editar/Deshabilitar
        r_prod_wh = cl_wh.get("/productos/")
        prod_wh_html = r_prod_wh.content.decode("utf-8")

        prod_count_after = Product.objects.count()

        # 4. Coherence contrast: minimum_stock=0 & sellable=0 + inactive + ?lote= writeoff tampering
        r_stock = cl_wh.get("/inventario/stock/")
        stock_html = r_stock.content.decode("utf-8")
        r_prods = cl_wh.get("/productos/")
        prods_html = r_prods.content.decode("utf-8")
        zero_row_stock = {
            "in_low_stock_banner": p_zero.name in [p.name for p in r_stock.context["low_stock"]],
            "stock_overview_badge_sin_stock_vendible": "Sin stock vendible" in stock_html,
            "product_list_badge_sin_stock_vigente": "Sin stock vigente" in prods_html,
            "product_list_badge_stock_bajo": "Stock bajo" in prods_html,
        }

        lote_cases = []
        for lbl, lparam in [
            ("expired_lot_uuid", str(lots["EXP-01"].pk)),
            ("upcoming_lot_uuid", str(lots["FUT-01"].pk)),
            ("nonexistent_uuid", str(uuid.uuid4())),
            ("malformed_str", "no-es-uuid"),
            ("nul_byte", "123\x00"),
        ]:
            resp = cl_wh.get("/inventario/bajas/nueva/?" + urlencode({"lote": lparam}))
            lote_cases.append({
                "case": lbl,
                "status": resp.status_code,
                "has_500": resp.status_code >= 500,
            })

        out = {
            "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "secondary_barcode_keys_for_agua": bkeys,
            "db_invariants": {
                "lot_count_before_after": [lot_count_before, lot_count_after],
                "prod_count_before_after": [prod_count_before, prod_count_after],
            },
            "header_matrix": header_matrix,
            "method_matrix": method_matrix,
            "dias_boundary_cases": dias_cases,
            "empty_with_error_dias_0": {
                "status": r_empty_err.status_code,
                "alerts": ext_e.alerts,
            },
            "q_boundary_cases": q_cases,
            "product_list_warehouse_has_actions": ("Editar" in prod_wh_html or "Deshabilitar" in prod_wh_html),
            "zero_minimum_zero_stock_contrast": zero_row_stock,
            "writeoff_lote_param_cases": lote_cases,
        }

        out_file = EVID_DIR / "probes-07b-fields-headers.json"
        out_file.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print("WROTE:", out_file)
        print("HEADERS /productos/ ADMIN:", [h for h in header_matrix if h["route"] == "/productos/" and h["role"] == "ADMIN"])
        print("EMPTY+ERR alerts:", out["empty_with_error_dias_0"])
        print("ZERO CONTRAST:", zero_row_stock)
        print("LOTE PARAM CASES:", lote_cases)
        print("PROD WH HAS ACTIONS:", out["product_list_warehouse_has_actions"])


if __name__ == "__main__":
    try:
        run()
    finally:
        connection.close()
        gc.collect()
        TMP_DIR.cleanup()
