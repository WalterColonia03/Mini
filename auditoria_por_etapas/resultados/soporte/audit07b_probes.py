from __future__ import annotations

import datetime
import html as html_lib
import json
import os
import re
import sys
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
R1_PMV = ROOT / "r1-pmv"
SOPORTE = Path(__file__).resolve().parent
EVID_DIR = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias" / "07-B-20261114"
DB_DIR = ROOT / "auditoria_por_etapas" / "resultados" / "datos" / "etapa07b-probes"

sys.path.insert(0, str(R1_PMV))
sys.path.insert(0, str(SOPORTE))

import audit07_run

EVID_DIR.mkdir(parents=True, exist_ok=True)
RUN_DIR, _, STAMP = audit07_run.make_run_dir("07b-probes")
DB_FILE = RUN_DIR / "audit.sqlite3"

os.environ["AUDIT07_RUN_DIR"] = str(RUN_DIR)
os.environ["AUDIT07_DEFAULT_COOKIES"] = "1"
os.environ["DJANGO_SETTINGS_MODULE"] = "audit07_settings"

import django

django.setup()

from django.core.management import call_command
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext, setup_test_environment
from django.utils import timezone

setup_test_environment()

from catalog.models import Category, Product
from catalog.services import toggle_category_status, toggle_product_availability
from identity.models import Account, Role
from identity.views import _dashboard_summary
from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff, Supplier
from inventory.services import (
    LotInput,
    confirm_initial_load,
    register_physical_adjustment,
    register_stock_entry,
    write_off_stock,
)
from cash.models import CashRegister
from cash.services import open_cash_shift
from sales.services import sellable_stock_for_product

call_command("migrate", verbosity=0)


def reset_db():
    call_command("flush", verbosity=0, interactive=False)
    CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})
    roles = {}
    for code, name in [
        (Role.Code.ADMIN, "Administrador"),
        (Role.Code.WAREHOUSE, "Almacenero"),
        (Role.Code.SELLER, "Vendedor"),
    ]:
        roles[code], _ = Role.objects.get_or_create(code=code, defaults={"name": name})
    admin = Account.objects.create_user("admin07b@test.invalid", "Password!2026", display_name="Admin 07B", role=roles[Role.Code.ADMIN])
    warehouse = Account.objects.create_user("alm07b@test.invalid", "Password!2026", display_name="Almacenero 07B", role=roles[Role.Code.WAREHOUSE])
    seller = Account.objects.create_user("vend07b@test.invalid", "Password!2026", display_name="Vendedor 07B", role=roles[Role.Code.SELLER])
    return admin, warehouse, seller


def make_client(user: Account | None = None) -> Client:
    c = Client(HTTP_HOST="localhost")
    if user is not None:
        c.force_login(user)
    return c


class _DOMNode:
    def __init__(self, tag: str, attrs: dict[str, str]):
        self.tag = tag
        self.attrs = attrs
        self.children: list[_DOMNode | str] = []

    @property
    def classes(self) -> list[str]:
        return (self.attrs.get("class") or "").split()

    def text(self) -> str:
        parts = []
        for ch in self.children:
            parts.append(ch if isinstance(ch, str) else ch.text())
        return " ".join("".join(parts).split())

    def find_all(self, predicate) -> list[_DOMNode]:
        out = []
        for ch in self.children:
            if isinstance(ch, _DOMNode):
                if predicate(ch):
                    out.append(ch)
                out.extend(ch.find_all(predicate))
        return out

    def find_first(self, predicate) -> _DOMNode | None:
        found = self.find_all(predicate)
        return found[0] if found else None


class _TreeParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _DOMNode("root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _DOMNode(tag.lower(), {k.lower(): (v or "") for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = _DOMNode(tag.lower(), {k.lower(): (v or "") for k, v in attrs})
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == tag:
                del self.stack[idx:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_dom(markup: str) -> _DOMNode:
    p = _TreeParser()
    p.feed(markup)
    return p.root


def parse_expirations_html(html_text: str) -> dict:
    dom = parse_dom(html_text)
    h1 = dom.find_first(lambda n: n.tag == "h1")
    h2 = dom.find_first(lambda n: n.tag == "h2")
    title = dom.find_first(lambda n: n.tag == "title")
    alerts = [el.text() for el in dom.find_all(lambda n: "alert" in n.classes)]
    summary_p = dom.find_first(lambda n: n.tag == "p" and "Total en pantalla" in n.text())
    rows = []
    tbl = dom.find_first(lambda n: n.tag == "table" and "expirations-table" in n.classes)
    tbody = tbl.find_first(lambda n: n.tag == "tbody") if tbl else None
    for tr in (tbody.find_all(lambda n: n.tag == "tr") if tbody else []):
        tds = [td.text() for td in tr.find_all(lambda n: n.tag == "td")]
        action_a = tr.find_first(lambda n: n.tag == "a")
        rows.append({
            "cells": tds,
            "action_href": action_a.attrs.get("href") if action_a else None,
            "action_text": action_a.text() if action_a else None,
        })
    days_input = dom.find_first(lambda n: n.tag == "input" and n.attrs.get("name") == "dias")
    return {
        "title": title.text() if title else None,
        "h1": h1.text() if h1 else None,
        "h2": h2.text() if h2 else None,
        "days_input_value": days_input.attrs.get("value") if days_input else None,
        "alerts": alerts,
        "summary": summary_p.text() if summary_p else None,
        "row_count": len(rows),
        "rows": rows,
        "has_separate_upcoming_section": bool(
            re.search(r"Próximos a vencer", html_text, re.I)
            and dom.find_first(lambda n: n.tag in {"h2", "h3"} and re.fullmatch(r"Vencidos", n.text(), re.I) is not None)
        ),
    }


def parse_stock_overview_html(html_text: str) -> dict:
    dom = parse_dom(html_text)
    h1 = dom.find_first(lambda n: n.tag == "h1")
    h2 = dom.find_first(lambda n: n.tag == "h2")
    banners = []
    for sec in dom.find_all(lambda n: "stock-alert-panel" in n.classes):
        h3 = sec.find_first(lambda n: n.tag == "h3")
        items = [li.text() for li in sec.find_all(lambda n: n.tag == "li")]
        banners.append({
            "heading": h3.text() if h3 else None,
            "summary_text": sec.text() if not h3 else None,
            "classes": sec.classes,
            "items": items,
        })
    products = []
    tbl = dom.find_first(lambda n: n.tag == "table" and "stock-overview-table" in n.classes)
    tbody = tbl.find_first(lambda n: n.tag == "tbody") if tbl else None
    for tr in (tbody.find_all(lambda n: n.tag == "tr") if tbody else []):
        tds = tr.find_all(lambda n: n.tag == "td")
        if len(tds) < 7:
            continue
        links = [{"text": a.text(), "href": a.attrs.get("href")} for a in tds[6].find_all(lambda n: n.tag == "a")]
        products.append({
            "product": tds[0].text(),
            "category": tds[1].text(),
            "physical": tds[2].text(),
            "physical_is_low_class": "stock-low" in tds[2].classes,
            "sellable": tds[3].text(),
            "sellable_is_low_class": "stock-low" in tds[3].classes,
            "minimum": tds[4].text(),
            "status": tds[5].text(),
            "links": links,
        })
    return {
        "h1": h1.text() if h1 else None,
        "h2": h2.text() if h2 else None,
        "banners": banners,
        "products": products,
    }


def sec_has_h3(node: _DOMNode) -> bool:
    return node.find_first(lambda ch: ch.tag == "h3") is not None


def parse_dashboard_response(resp) -> dict:
    html_text = resp.content.decode()
    dom = parse_dom(html_text)
    h1 = dom.find_first(lambda n: n.tag == "h1")
    h2 = dom.find_first(lambda n: n.tag == "h2")
    cards = []
    for art in dom.find_all(lambda n: n.tag in {"article", "div"} and any("summary" in c or "kpi" in c or "metric" in c for c in n.classes)):
        cards.append(art.text())
    nav_links = [{"text": a.text(), "href": a.attrs.get("href")} for a in dom.find_all(lambda n: n.tag == "a") if a.attrs.get("href", "").startswith("/")]
    kpis = {}
    for card in dom.find_all(lambda n: "kpi-card" in n.classes or "metric-card" in n.classes or "stat-card" in n.classes or n.tag == "dl"):
        kpis.update({dt.text(): dd.text() for dt, dd in zip(card.find_all(lambda n: n.tag == "dt"), card.find_all(lambda n: n.tag == "dd"))})
    return {
        "status_code": resp.status_code,
        "h1": h1.text() if h1 else None,
        "h2": h2.text() if h2 else None,
        "context_summary": dict(resp.context["summary"]) if (resp.context and resp.context.get("summary")) else None,
        "kpis": kpis,
        "has_resumen_general": "Resumen general" in html_text,
        "nav_links": nav_links,
    }


def parse_product_list_html(html_text: str) -> list[dict]:
    dom = parse_dom(html_text)
    out = []
    tbl = dom.find_first(lambda n: n.tag == "table" and "catalog-products" in n.classes)
    tbody = tbl.find_first(lambda n: n.tag == "tbody") if tbl else None
    for tr in (tbody.find_all(lambda n: n.tag == "tr") if tbody else []):
        tds = tr.find_all(lambda n: n.tag == "td")
        if len(tds) < 8:
            continue
        badge = tds[4].find_first(lambda n: "badge" in n.classes or "status" in n.classes)
        out.append({
            "name": tds[0].text(),
            "barcode": tds[1].text(),
            "category": tds[2].text(),
            "price": tds[3].text(),
            "stock_cell": tds[4].text(),
            "low_badge": badge.text() if badge else None,
            "minimum": tds[5].text(),
            "status": tds[6].text(),
        })
    return out


results: dict = {
    "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "cases": {},
}

# ==============================================================================
# CASE 0: Empty DB (0 products, 0 lots) across views & dashboard
# ==============================================================================
admin, warehouse, seller = reset_db()
empty_stock = parse_stock_overview_html(make_client(warehouse).get("/inventario/stock/").content.decode())
empty_exp = parse_expirations_html(make_client(warehouse).get("/productos/vencimientos/").content.decode())
empty_dash_admin = parse_dashboard_response(make_client(admin).get("/inicio/"))
empty_dash_wh = parse_dashboard_response(make_client(warehouse).get("/inicio/"))
empty_dash_seller = parse_dashboard_response(make_client(seller).get("/inicio/"))
results["cases"]["empty_db"] = {
    "stock": empty_stock,
    "expirations": empty_exp,
    "dashboard_admin": empty_dash_admin,
    "dashboard_warehouse": empty_dash_wh,
    "dashboard_seller": empty_dash_seller,
}

# ==============================================================================
# CASE 1: CP-HU-PROD-06-001 (exact data at 2026-11-12 Lima + midnight UTC/Lima)
# ==============================================================================
admin, warehouse, seller = reset_db()
cat = Category.objects.create(name="Lácteos")
sup = Supplier.objects.create(name="Distribuidora Lima", ruc="20123456789")
p_yog = Product.objects.create(
    name="Yogurt Natural 1L", category=cat, barcode="7750006000011", unit="UND",
    sale_price=Decimal("8.50"), minimum_stock=5, is_active=True, controls_expiration=True,
)
p_inact = Product.objects.create(
    name="Producto E Caducado", category=cat, barcode="7750006000028", unit="UND",
    sale_price=Decimal("5.00"), minimum_stock=2, is_active=True, controls_expiration=True,
)

# Register initial loads at frozen time 2026-11-10 15:00Z (Lima 2026-11-10)
t_setup = datetime.datetime(2026, 11, 10, 15, 0, tzinfo=datetime.timezone.utc)
with patch("django.utils.timezone.now", return_value=t_setup):
    confirm_initial_load(
        actor=warehouse,
        product=p_yog,
        supplier=sup,
        lots=[
            LotInput(number="LOTE-A", quantity=10, unit_cost=Decimal("5.0000"), expiration_date=datetime.date(2026, 11, 13)),
            LotInput(number="LOTE-B", quantity=10, unit_cost=Decimal("5.0000"), expiration_date=datetime.date(2026, 12, 12)),
        ],
    )
    confirm_initial_load(
        actor=warehouse,
        product=p_inact,
        supplier=sup,
        lots=[
            LotInput(number="LOTE-E", quantity=3, unit_cost=Decimal("3.0000"), expiration_date=datetime.date(2026, 11, 12)),
        ],
    )

# Deactivate Producto E per CP-HU-PROD-06-001 step 5
toggle_product_availability(actor=admin, product=p_inact)

c_wh = make_client(warehouse)
c_ad = make_client(admin)

# Check Lima midnight transition: 04:59:59Z (= Nov 11 23:59:59 Lima) vs 05:00:00Z (= Nov 12 00:00:00 Lima)
midnight_transitions = {}
for label, ts in [
    ("before_midnight_lima_235959", datetime.datetime(2026, 11, 12, 4, 59, 59, tzinfo=datetime.timezone.utc)),
    ("at_midnight_lima_000000", datetime.datetime(2026, 11, 12, 5, 0, 0, tzinfo=datetime.timezone.utc)),
]:
    with patch("django.utils.timezone.now", return_value=ts):
        p_inact.refresh_from_db()
        resp = c_wh.get("/productos/vencimientos/?dias=30")
        parsed = parse_expirations_html(resp.content.decode())
        midnight_transitions[label] = {
            "lima_localdate": str(timezone.localdate()),
            "p_inact_physical": p_inact.physical_stock,
            "p_inact_sellable_if_active": p_inact.sellable_stock,
            "summary": parsed["summary"],
            "rows": parsed["rows"],
        }

t_nov12 = datetime.datetime(2026, 11, 12, 15, 0, tzinfo=datetime.timezone.utc)
filter_probes = {}
with patch("django.utils.timezone.now", return_value=t_nov12):
    for key, qs in [
        ("default_no_param", ""),
        ("empty", "?dias="),
        ("spaces", "?dias=%20%207%20%20"),
        ("leading_zeros_7", "?dias=00007"),
        ("dias_1", "?dias=1"),
        ("dias_7", "?dias=7"),
        ("dias_30", "?dias=30"),
        ("dias_3650", "?dias=3650"),
        ("dias_0", "?dias=0"),
        ("dias_0000", "?dias=0000"),
        ("dias_neg0", "?dias=-0"),
        ("dias_neg5", "?dias=-5"),
        ("dias_3651", "?dias=3651"),
        ("dias_huge", "?dias=999999999999999999"),
        ("dias_abc", "?dias=abc"),
        ("dias_plus7", "?dias=%2B7"),
        ("dias_decimal", "?dias=7.5"),
        ("dias_arabic_digit", "?dias=\u0665"),
        ("dias_nul", "?dias=1%00"),
        ("repeated_7_then_30", "?dias=7&dias=30"),
        ("repeated_7_then_abc", "?dias=7&dias=abc"),
    ]:
        r = c_wh.get(f"/productos/vencimientos/{qs}")
        p_dom = parse_expirations_html(r.content.decode())
        filter_probes[key] = {
            "status_code": r.status_code,
            "days_input_value": p_dom["days_input_value"],
            "alerts": p_dom["alerts"],
            "summary": p_dom["summary"],
            "row_count": p_dom["row_count"],
            "lot_numbers": [row["cells"][2] for row in p_dom["rows"]],
            "states": [row["cells"][5] for row in p_dom["rows"]],
            "has_separate_upcoming_section": p_dom["has_separate_upcoming_section"],
        }
    stock_nov12 = parse_stock_overview_html(c_wh.get("/inventario/stock/").content.decode())
    prod_list_nov12 = parse_product_list_html(c_ad.get("/productos/").content.decode())
    dash_ad_nov12 = parse_dashboard_response(c_ad.get("/inicio/"))
    dash_wh_nov12 = parse_dashboard_response(c_wh.get("/inicio/"))

results["cases"]["cp_hu_prod_06_001"] = {
    "midnight_transitions": midnight_transitions,
    "filter_probes": filter_probes,
    "stock_overview_nov12": stock_nov12,
    "product_list_nov12": prod_list_nov12,
    "dashboard_admin_nov12": dash_ad_nov12,
    "dashboard_warehouse_nov12": dash_wh_nov12,
}

# ==============================================================================
# CASE 2: CP-DEC-07-VENCIDOS-FILTRO-001 + Category Reactivation + Zero/Mixed Lots + Min=0 + Origins
# ==============================================================================
admin, warehouse, seller = reset_db()
cat_granos = Category.objects.create(name="Granos")
cat_beb = Category.objects.create(name="Bebidas")
sup = Supplier.objects.create(name="Proveedor Central", ruc="20555666777")

p_arroz = Product.objects.create(
    name="Arroz Costeño", category=cat_granos, barcode="7750007000018", unit="UND",
    sale_price=Decimal("4.20"), minimum_stock=10, is_active=True, controls_expiration=True,
)
p_inact_exp = Product.objects.create(
    name="Producto E Vencido Inactivo", category=cat_granos, barcode="7750007000025", unit="UND",
    sale_price=Decimal("6.00"), minimum_stock=5, is_active=True, controls_expiration=True,
)
p_susp_indiv = Product.objects.create(
    name="Gaseosa Suspendida Previa", category=cat_beb, barcode="7750007000032", unit="UND",
    sale_price=Decimal("3.00"), minimum_stock=10, is_active=True, controls_expiration=True,
)
p_beb_act = Product.objects.create(
    name="Agua Mineral Mixta", category=cat_beb, barcode="7750007000049", unit="UND",
    sale_price=Decimal("2.50"), minimum_stock=10, is_active=True, controls_expiration=True,
)
p_min_zero = Product.objects.create(
    name="Sal Sin Minimo Cero Stock", category=cat_granos, barcode="7750007000056", unit="UND",
    sale_price=Decimal("1.50"), minimum_stock=0, is_active=True, controls_expiration=True,
)
p_zero_lot = Product.objects.create(
    name="Fideos Lote Agotado", category=cat_granos, barcode="7750007000063", unit="UND",
    sale_price=Decimal("3.80"), minimum_stock=2, is_active=True, controls_expiration=True,
)

t_load = datetime.datetime(2026, 11, 10, 15, 0, tzinfo=datetime.timezone.utc)
with patch("django.utils.timezone.now", return_value=t_load):
    # Arroz: 5 units exp Nov 13 (+1d from Nov 12), plus +30d (Dec 12) and +31d (Dec 13) -> wait keep Arroz = 5 total for exact CP-DEC-07 low stock!
    confirm_initial_load(
        actor=warehouse, product=p_arroz, supplier=sup,
        lots=[LotInput(number="AR-1D", quantity=5, unit_cost=Decimal("2.5000"), expiration_date=datetime.date(2026, 11, 13))],
    )
    confirm_initial_load(
        actor=warehouse, product=p_inact_exp, supplier=sup,
        lots=[LotInput(number="PE-EXP", quantity=3, unit_cost=Decimal("4.0000"), expiration_date=datetime.date(2026, 11, 12))],
    )
    confirm_initial_load(
        actor=warehouse, product=p_susp_indiv, supplier=sup,
        lots=[LotInput(number="GAS-30D", quantity=4, unit_cost=Decimal("1.5000"), expiration_date=datetime.date(2026, 12, 12))],
    )
    # Agua Mineral Mixta: 10 unexpired (+30d and +31d boundary + tie break), plus 7 expired discovered via PhysicalAdjustment!
    confirm_initial_load(
        actor=warehouse, product=p_beb_act, supplier=sup,
        lots=[
            LotInput(number="AG-30D", quantity=4, unit_cost=Decimal("1.0000"), expiration_date=datetime.date(2026, 12, 12)),
            LotInput(number="AG-31D", quantity=6, unit_cost=Decimal("1.0000"), expiration_date=datetime.date(2026, 12, 13)),
        ],
    )
    # Fideos: 1 lot exhausted to 0 via PhysicalAdjustment (-3)
    confirm_initial_load(
        actor=warehouse, product=p_zero_lot, supplier=sup,
        lots=[LotInput(number="FID-ZERO", quantity=3, unit_cost=Decimal("2.0000"), expiration_date=datetime.date(2026, 11, 15))],
    )
    # StockReceipt posterior on Agua (with supplier)
    register_stock_entry(
        actor=warehouse, product=p_beb_act, supplier=sup,
        lots=[LotInput(number="AG-REC-30D", quantity=0 if False else 1, unit_cost=Decimal("1.1000"), expiration_date=datetime.date(2026, 12, 12))],
    )

# Adjust on Nov 12: deplete FID-ZERO to 0, add expired lot via PhysicalAdjustment on Agua (supplier=None)
t_nov12 = datetime.datetime(2026, 11, 12, 16, 0, tzinfo=datetime.timezone.utc)
with patch("django.utils.timezone.now", return_value=t_nov12):
    lot_fid = Lot.objects.get(number_normalized="FID-ZERO")
    write_off_stock(actor=warehouse, lot=lot_fid, quantity=3, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura total")
    # Wait: PhysicalAdjustment new_lot on Agua: 6 expired + 10 unexpired = 17 physical vs 11 sellable; let's check Agua exact numbers:
    # Initial 4+6=10, Receipt +1=11 unexpired. Add 6 expired via PhysicalAdjustment -> 17 physical, 11 sellable (min=10: sellable NOT low).
    # Wait let's make AG-REC-30D NOT there, or set p_beb_act.minimum_stock = 11 so physical=17 (>11) and sellable=11 (<=11)!
    register_physical_adjustment(
        actor=admin, product=p_beb_act, number="AG-ADJ-EXP",
        expiration_date=datetime.date(2026, 11, 12), delta=6, reason="Hallazgo lote vencido en conteo",
    )
    p_beb_act.minimum_stock = 11
    p_beb_act.save(update_fields=["minimum_stock"])

# Suspend PE and p_susp_indiv individually; then toggle cat_beb OFF and back ON!
toggle_product_availability(actor=admin, product=p_inact_exp)
toggle_product_availability(actor=admin, product=p_susp_indiv)
toggle_category_status(actor=admin, category=cat_beb, is_active=False)
cat_beb.refresh_from_db()
toggle_category_status(actor=admin, category=cat_beb, is_active=True)
p_susp_indiv.refresh_from_db()
p_beb_act.refresh_from_db()

c_ad = make_client(admin)
c_wh = make_client(warehouse)
c_se = make_client(seller)
c_anon = make_client(None)

with patch("django.utils.timezone.now", return_value=t_nov12):
    exp_7 = parse_expirations_html(c_wh.get("/productos/vencimientos/?dias=7").content.decode())
    exp_30 = parse_expirations_html(c_wh.get("/productos/vencimientos/?dias=30").content.decode())
    exp_31 = parse_expirations_html(c_wh.get("/productos/vencimientos/?dias=31").content.decode())
    stock_ad = parse_stock_overview_html(c_ad.get("/inventario/stock/").content.decode())
    stock_wh = parse_stock_overview_html(c_wh.get("/inventario/stock/").content.decode())
    prod_ad = parse_product_list_html(c_ad.get("/productos/").content.decode())
    dash_ad = parse_dashboard_response(c_ad.get("/inicio/"))
    dash_wh = parse_dashboard_response(c_wh.get("/inicio/"))
    dash_se = parse_dashboard_response(c_se.get("/inicio/"))

    # POS sellable contrast & open shift
    open_cash_shift(actor=seller, opening_amount=Decimal("50.00"))
    pos_arroz = c_se.get("/ventas/?query=Arroz").content.decode()
    pos_agua = c_se.get("/ventas/?query=Agua").content.decode()
    pos_inact = c_se.get("/ventas/?query=Gaseosa").content.decode()
    pos_exp = c_se.get("/ventas/?query=Producto+E").content.decode()
    pos_agua_sellable_service = sellable_stock_for_product(p_beb_act)

    # N+1 Query invariant test: check query count with current products vs +5 extra products
    with override_settings(DEBUG=True):
        with CaptureQueriesContext(connection) as q_stock_before:
            r_sb = c_wh.get("/inventario/stock/")
        assert r_sb.status_code == 200
        n_stock_before = len(q_stock_before)
        with CaptureQueriesContext(connection) as q_exp_before:
            r_eb = c_wh.get("/productos/vencimientos/")
        assert r_eb.status_code == 200
        n_exp_before = len(q_exp_before)
        with CaptureQueriesContext(connection) as q_dash_before:
            r_db = c_ad.get("/inicio/")
        assert r_db.status_code == 200
        n_dash_before = len(q_dash_before)

        for idx in range(5):
            px = Product.objects.create(
                name=f"Extra Producto {idx}", category=cat_granos, barcode=f"77500079000{idx}1", unit="UND",
                sale_price=Decimal("2.00"), minimum_stock=5, is_active=True, controls_expiration=True,
            )
            confirm_initial_load(
                actor=warehouse, product=px, supplier=sup,
                lots=[LotInput(number=f"EX-{idx}", quantity=2, unit_cost=Decimal("1.0000"), expiration_date=datetime.date(2026, 11, 20))],
            )

        with CaptureQueriesContext(connection) as q_stock_after:
            r_sa = c_wh.get("/inventario/stock/")
        assert r_sa.status_code == 200
        n_stock_after = len(q_stock_after)
        with CaptureQueriesContext(connection) as q_exp_after:
            r_ea = c_wh.get("/productos/vencimientos/")
        assert r_ea.status_code == 200
        n_exp_after = len(q_exp_after)
        with CaptureQueriesContext(connection) as q_dash_after:
            r_da = c_ad.get("/inicio/")
        assert r_da.status_code == 200
        n_dash_after = len(q_dash_after)

    # HTTP Method & Permission Matrix & Cache headers
    auth_matrix = {}
    for route in ["/inventario/stock/", "/productos/vencimientos/"]:
        r_anon = c_anon.get(route)
        r_se = c_se.get(route)
        r_wh_get = c_wh.get(route)
        r_wh_post = c_wh.post(route)
        r_wh_put = c_wh.put(route)
        r_wh_del = c_wh.delete(route)
        r_ad_post = c_ad.post(route)
        auth_matrix[route] = {
            "anon_status": r_anon.status_code,
            "anon_location": r_anon.get("Location"),
            "seller_status": r_se.status_code,
            "warehouse_get_status": r_wh_get.status_code,
            "warehouse_cache_control": r_wh_get.get("Cache-Control"),
            "warehouse_post_status": r_wh_post.status_code,
            "warehouse_put_status": r_wh_put.status_code,
            "warehouse_delete_status": r_wh_del.status_code,
            "admin_post_status": r_ad_post.status_code,
        }

results["cases"]["cp_dec_07_and_edge_cases"] = {
    "p_susp_indiv_is_active_after_cat_reactivate": p_susp_indiv.is_active,
    "p_beb_act_physical": p_beb_act.physical_stock,
    "p_beb_act_sellable": p_beb_act.sellable_stock,
    "pos_agua_sellable_service": pos_agua_sellable_service,
    "pos_contains_agua_11": ("<td>11</td>" in pos_agua),
    "pos_excludes_gaseosa_susp": ("Gaseosa Suspendida Previa" not in pos_inact),
    "pos_excludes_producto_e": ("Producto E Vencido Inactivo" not in pos_exp),
    "exp_dias_7": exp_7,
    "exp_dias_30": exp_30,
    "exp_dias_31": exp_31,
    "stock_overview_admin": stock_ad,
    "stock_overview_warehouse": stock_wh,
    "product_list_admin": prod_ad,
    "dashboard_admin": dash_ad,
    "dashboard_warehouse": dash_wh,
    "dashboard_seller": dash_se,
    "query_counts": {
        "stock_before_5extra": n_stock_before,
        "stock_after_5extra": n_stock_after,
        "exp_before_5extra": n_exp_before,
        "exp_after_5extra": n_exp_after,
        "dash_before_5extra": n_dash_before,
        "dash_after_5extra": n_dash_after,
    },
    "auth_and_http_matrix": auth_matrix,
}

# Clean up probe DB file connections
connection.close()

out_path = EVID_DIR / "probes-07b.json"
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("WROTE:", out_path)
print("MIDNIGHT_BEFORE:", midnight_transitions["before_midnight_lima_235959"]["summary"])
print("MIDNIGHT_AFTER:", midnight_transitions["at_midnight_lima_000000"]["summary"])
print("EXP_7_ROWS:", exp_7["row_count"], "SEPARATE:", exp_7["has_separate_upcoming_section"], "SUMMARY:", exp_7["summary"])
print("QUERY_COUNTS:", results["cases"]["cp_dec_07_and_edge_cases"]["query_counts"])
print("DASH_ADMIN:", dash_ad)
