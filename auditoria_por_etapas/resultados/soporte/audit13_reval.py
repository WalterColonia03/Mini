"""Stage 13 deep revalidation runner on isolated SQLite DBs (no product edits)."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sys
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
R1 = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas" / "resultados"
SOPORTE = RESULTS / "soporte"
EVID = RESULTS / "evidencias" / "13-reval-20261115"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_run_dir(prefix: str = "etapa13-reval-") -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = RESULTS / "datos" / f"{prefix}{stamp}-{secrets.token_hex(4)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return run_dir


def boot_django(run_dir: Path, pg_env: dict[str, str] | None = None):
    os.environ["AUDIT13_REVAL_RUN_DIR"] = str(run_dir)
    if pg_env:
        os.environ.update(pg_env)
    sys.path.insert(0, str(R1))
    sys.path.insert(0, str(SOPORTE))
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit13_reval_settings"
    import django
    django.setup()


def seed_populated(run_dir: Path) -> dict:
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from identity.models import Role
    from inventory.models import InitialInventoryLoad, Lot
    from sales.models import Sale, SaleDraft, SaleDraftLine, SaleLine

    User = get_user_model()
    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    creds = {}
    users = {}
    for key, email, name, role in [
        ("ADMIN", "admin13r@test.invalid", "Admin Reval", r_admin),
        ("ALMACENERO", "almacen13r@test.invalid", "Almacén Reval", r_wh),
        ("VENDEDOR", "vendedor13r1@test.invalid", "Vendedor Uno", r_sel),
        ("VENDEDOR2", "vendedor13r2@test.invalid", "Vendedor Dos", r_sel),
    ]:
        pw = "P@ss-" + secrets.token_urlsafe(12)
        u = User.objects.create_user(email=email, password=pw, display_name=name, role=role)
        creds[key] = {"email": email, "password": pw, "display_name": name, "role": role.code}
        users[key] = u
    (run_dir / ".credentials.json").write_text(json.dumps(creds, indent=2), encoding="utf-8")

    cat_act = Category.objects.create(name="Abarrotes Reval", is_active=True)
    cat_inact = Category.objects.create(name="Congelados Inact", is_active=False)

    today = timezone.localdate()
    almacen = users["ALMACENERO"]

    def make_prod(name, bc, min_stk, price, active=True, cat=cat_act, lots=()):
        p = Product.objects.create(
            category=cat, name=name, barcode=bc, sale_price=Decimal(price),
            is_active=active, minimum_stock=min_stk,
        )
        if lots:
            load = InitialInventoryLoad.objects.create(product=p, responsible=almacen)
            for idx, (delta_d, avail) in enumerate(lots, 1):
                Lot.objects.create(
                    product=p, initial_load=load, responsible=almacen,
                    number=f"{bc}-L{idx}", initial_quantity=max(1, avail),
                    available_quantity=avail, unit_cost=Decimal("2.5000"),
                    expiration_date=today + timedelta(days=delta_d),
                )
        return p

    # 1. Exact equality & window boundaries
    p_crit = make_prod("Arroz Critico 13", "775000013001", 5, "4.50", True, cat_act, [(1, 2), (30, 3)])
    p_zero = make_prod("Leche Agotada 13", "775000013002", 0, "3.20", True, cat_act, [])
    p_ok = make_prod("Aceite Sano 13", "775000013003", 5, "9.90", True, cat_act, [(31, 20), (5, 0)])
    p_inact = make_prod("Fideo Inactivo 13", "775000013004", 99, "2.80", False, cat_act, [(0, 7), (30, 4), (3, 3)])
    p_inact_cat = make_prod("Helado CatInact 13", "775000013005", 10, "6.00", True, cat_inact, [(15, 2)])
    p_mix7 = make_prod("Yogurt Ventana7 13", "775000013006", 2, "5.50", True, cat_act, [(-2, 2), (4, 6)])

    # Expiring (>today, <=today+30, avail>0):
    # p_crit: (1,2), (30,3) -> 2
    # p_ok: (31,20) out, (5,0) zero -> 0
    # p_inact: (30,4), (3,3) -> 2  [note: (0,7) is expired]
    # p_inact_cat: (15,2) -> 1
    # p_mix7: (4,6) -> 1 [note: (-2,2) is expired]
    # Total expiring = 6, expired = 2, low_stock (active & active cat, avail<=min) = 2 (p_crit=5<=5, p_zero=0<=0; p_mix7=6>2)

    reg1 = CashRegister.objects.create(code="CAJA-R1")
    reg2 = CashRegister.objects.create(code="CAJA-R2")
    closed_shift = CashShift.objects.create(
        cash_register=reg1, seller=users["VENDEDOR"], opening_amount=Decimal("50.00"),
        status=CashShift.Status.CLOSED,
    )
    open_shift = CashShift.objects.create(
        cash_register=reg2, seller=users["VENDEDOR2"], opening_amount=Decimal("100.00"),
        status=CashShift.Status.OPEN,
    )

    day_start = timezone.make_aware(datetime.combine(today, time.min))
    specs = [
        ("V-13R00001", closed_shift, users["VENDEDOR"], day_start - timedelta(microseconds=1), "19.90", "1.00", "20.00", "0.10"),
        ("V-13R00002", closed_shift, users["VENDEDOR"], day_start, "1234.50", "12.34", "1250.00", "15.50"),
        ("V-13R00003", open_shift, users["VENDEDOR2"], day_start + timedelta(days=1) - timedelta(microseconds=1), "5.49", "0.01", "10.00", "4.51"),
        ("V-13R00004", open_shift, users["VENDEDOR2"], day_start + timedelta(days=1), "99.99", "9.99", "100.00", "0.01"),
    ]
    for corr, sh, sel, ts, tot, disc, rec, chg in specs:
        tot_d = Decimal(tot)
        base_d = (tot_d / Decimal("1.18")).quantize(Decimal("0.01"))
        igv_d = tot_d - base_d
        s = Sale.objects.create(
            cash_shift=sh, seller=sel, total_amount=tot_d, base_amount=base_d,
            igv_amount=igv_d, discount_amount=Decimal(disc), cash_received=Decimal(rec),
            change_given=Decimal(chg), correlative=corr, idempotency_key=uuid4(),
            seller_snapshot_name=sel.display_name, cash_register_snapshot_code=sh.cash_register.code,
        )
        Sale.objects.filter(pk=s.pk).update(confirmed_at=ts)
        SaleLine.objects.create(
            sale=s, product=p_ok, product_name_snapshot=p_ok.name, barcode_snapshot=p_ok.barcode,
            quantity=1, unit_price=tot_d, line_subtotal=tot_d, unit_cost=Decimal("2.5000"),
        )

    # Active draft must NOT be counted as confirmed sale
    draft = SaleDraft.objects.create(cash_shift=open_shift, seller=users["VENDEDOR2"])
    SaleDraftLine.objects.create(draft=draft, product=p_ok, quantity=2)

    return {
        "today": today.isoformat(),
        "expected": {
            "expiring": 6,
            "expired": 2,
            "low_stock": 2,
            "sales_count": 2,
            "sales_total": "1239.99",
            "discount_total": "12.35",
            "open_shifts": 1,
        },
        "products": {
            "crit": p_crit.pk, "zero": p_zero.pk, "ok": p_ok.pk,
            "inact": p_inact.pk, "inact_cat": p_inact_cat.pk, "mix7": p_mix7.pk,
        },
    }


def extract_cards(html: str) -> dict[str, str]:
    pairs = re.findall(r'<article class="stat-card[^"]*">\s*<p class="stat-label">(.*?)</p>\s*<p class="stat-value">(.*?)</p>', html, re.S)
    return {re.sub(r"\s+", " ", k).strip(): re.sub(r"\s+", " ", v).strip() for k, v in pairs}


def run_probes() -> dict:
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from identity.models import Role
    from identity.views import _dashboard_summary

    EVID.mkdir(parents=True, exist_ok=True)
    protected_db = R1 / "r1_pmv.sqlite3"
    protected_before = sha256_file(protected_db)

    run_dir = make_run_dir("etapa13-reval-")
    boot_django(run_dir)
    call_command("migrate", verbosity=0)
    fixture = seed_populated(run_dir)
    creds = json.loads((run_dir / ".credentials.json").read_text(encoding="utf-8"))

    checks = []

    def check(cid, ok, detail):
        checks.append({"id": cid, "ok": bool(ok), "detail": detail})
        if not ok:
            print(f"FAIL {cid}: {detail}")

    # 1. SQL Snapshot & Query Budget
    from django.utils import timezone
    today = timezone.localdate()
    with CaptureQueriesContext(connection) as q_adm:
        s_adm = _dashboard_summary(Role.Code.ADMIN, today)
    with CaptureQueriesContext(connection) as q_wh:
        s_wh = _dashboard_summary(Role.Code.WAREHOUSE, today)
    with CaptureQueriesContext(connection) as q_sel:
        s_sel = _dashboard_summary(Role.Code.SELLER, today)

    exp = fixture["expected"]
    check("SQL-ADMIN-ONE-QUERY", len(q_adm) == 1 and "CROSS JOIN" in q_adm[0]["sql"], {"queries": len(q_adm)})
    check("SQL-ADMIN-VALUES", {
        **s_adm,
        "sales_total": f"{s_adm['sales_total']:.2f}",
        "discount_total": f"{s_adm['discount_total']:.2f}",
    } == exp, {"actual": str(s_adm), "expected": exp})
    check("SQL-WH-NO-SALES-CASH", len(q_wh) == 1 and "sales_sale" not in q_wh[0]["sql"] and "cash_cashshift" not in q_wh[0]["sql"], {
        "summary": s_wh, "queries": len(q_wh)
    })
    check("SQL-SELLER-NONE-0Q", s_sel is None and len(q_sel) == 0, {"summary": s_sel, "queries": len(q_sel)})

    # 2. HTTP /inicio/ per role + HMAC proof + headers
    client_anon = Client()
    r_anon = client_anon.get("/inicio/")
    check("ANON-INIT-302", r_anon.status_code == 302 and "/?next=/inicio/" in r_anon.url, {"status": r_anon.status_code, "url": r_anon.url})

    role_cards = {}
    for rkey in ["ADMIN", "ALMACENERO", "VENDEDOR"]:
        c = Client()
        nonce = secrets.token_hex(32)
        assert c.login(email=creds[rkey]["email"], password=creds[rkey]["password"])
        resp = c.get("/inicio/", HTTP_X_AUDIT13_CHALLENGE=nonce)
        expected_proof = hmac.new(settings.SECRET_KEY.encode(), nonce.encode(), hashlib.sha256).hexdigest()
        html = resp.content.decode("utf-8")
        cards = extract_cards(html)
        role_cards[rkey] = {
            "cards": cards,
            "cache_control": resp.get("Cache-Control", ""),
            "x_request_id": resp.get("X-Request-ID", ""),
            "hrefs": sorted(set(re.findall(r'href="(/[^"]*)"', html))),
        }
        check(f"PROOF-{rkey}", resp.get("X-Audit13-Proof") == expected_proof and resp.status_code == 200, {"status": resp.status_code})
        cc = resp.get("Cache-Control", "")
        check(f"NO-STORE-{rkey}", all(tok in cc for tok in ("no-store", "no-cache", "must-revalidate")), {"cc": cc})

    # Verify exact UI rendered values vs SQL, Lima date label, and refresh guidance
    adm_dash_html0 = Client()
    adm_dash_html0.login(email=creds["ADMIN"]["email"], password=creds["ADMIN"]["password"])
    adm_html_full = adm_dash_html0.get("/inicio/").content.decode("utf-8")
    expected_date_pe = today.strftime("%d/%m/%Y")
    adm_cards = role_cards["ADMIN"]["cards"]
    check("HTML-ADMIN-METRICS", (
        adm_cards.get("Ventas de hoy") == "2"
        and adm_cards.get("Total vendido hoy") == "S/ 1239,99"
        and adm_cards.get("Descuentos aplicados hoy") == "S/ 12,35"
        and adm_cards.get("Turnos abiertos ahora") == "1"
        and adm_cards.get("Stock en nivel crítico") == "2"
        and adm_cards.get("Lotes por vencer (30 días)") == "6"
        and adm_cards.get("Lotes vencidos con stock") == "2"
        and f"Resumen del {expected_date_pe}" in adm_html_full
        and "hora de Lima" in adm_html_full
        and "Recarga la página" in adm_html_full
        and f'/ventas/historial/?fecha={fixture["today"]}' in adm_html_full
        and "/inventario/stock/" in adm_html_full
        and "/productos/vencimientos/" in adm_html_full
        and "/caja/turnos/" in adm_html_full
    ), {"cards": adm_cards, "date_pe": expected_date_pe})
    wh_cards = role_cards["ALMACENERO"]["cards"]
    check("HTML-WH-METRICS", (
        len(wh_cards) == 3
        and wh_cards.get("Stock en nivel crítico") == "2"
        and wh_cards.get("Lotes por vencer (30 días)") == "6"
        and wh_cards.get("Lotes vencidos con stock") == "2"
    ), wh_cards)
    check("HTML-SELLER-NO-METRICS", len(role_cards["VENDEDOR"]["cards"]) == 0, role_cards["VENDEDOR"]["cards"])

    # 3. Linked destinations & Parity (ADMIN)
    c_adm = Client()
    c_adm.login(email=creds["ADMIN"]["email"], password=creds["ADMIN"]["password"])
    r_stock = c_adm.get("/inventario/stock/")
    ctx_stock = r_stock.context
    check("PARITY-E01-STOCK", (
        r_stock.status_code == 200
        and len(ctx_stock["low_stock"]) == 2
        and ctx_stock["expiring_lots"].count() == 6
        and ctx_stock["expired_lots"].count() == 2
    ), {
        "low_stock": [p.name for p in ctx_stock["low_stock"]],
        "expiring_count": ctx_stock["expiring_lots"].count(),
        "expired_count": ctx_stock["expired_lots"].count(),
    })

    r_exp30 = c_adm.get("/productos/vencimientos/")
    r_exp7 = c_adm.get("/productos/vencimientos/", {"dias": "7"})
    r_exp_bad = c_adm.get("/productos/vencimientos/", {"dias": "abc"})
    r_exp_hi = c_adm.get("/productos/vencimientos/", {"dias": "3651"})
    exp7_html = r_exp7.content.decode("utf-8")
    # Observe DEC-07/C-02 truthfully (does ?dias=7 show expired lots inside the single expiring table?)
    exp7_ctx_count = r_exp7.context["lots"].count() if hasattr(r_exp7.context["lots"], "count") else len(r_exp7.context["lots"])
    exp7_has_expired = "Vencido" in exp7_html
    check("LINK-E02-EXPIRATIONS", (
        r_exp30.status_code == 200
        and r_exp7.status_code == 200
        and r_exp_bad.status_code == 200 and "mostrando los próximos 30 días" in r_exp_bad.content.decode("utf-8")
        and r_exp_hi.status_code == 200 and "mostrando los próximos 30 días" in r_exp_hi.content.decode("utf-8")
    ), {
        "exp30_count": len(r_exp30.context["lots"]),
        "exp7_count": exp7_ctx_count,
        "exp7_mixes_expired": exp7_has_expired,
        "inact_expired_badge_present": "Fideo Inactivo 13" in r_exp30.content.decode("utf-8") and "Producto inactivo" in r_exp30.content.decode("utf-8"),
    })

    r_vh = c_adm.get("/ventas/historial/", {"fecha": fixture["today"]})
    check("PARITY-E03-SALES-TODAY", (
        r_vh.status_code == 200
        and r_vh.context["sales_count"] == 2
        and r_vh.context["total_vendido"] == Decimal("1239.99")
        and r_vh.context["total_descuento"] == Decimal("12.35")
    ), {
        "count": r_vh.context["sales_count"],
        "total": str(r_vh.context["total_vendido"]),
        "discount": str(r_vh.context["total_descuento"]),
    })

    # D11 & history boundary tests on BOTH /ventas/historial/ and /caja/turnos/
    d11_results = {}
    for route, param, bad in [
        ("/ventas/historial/", "fecha", "2026-02-30"),
        ("/ventas/historial/", "fecha_hasta", "9999-12-31"),
        ("/ventas/historial/", "q", "V-\x0013"),
        ("/ventas/historial/", "page", "999"),
        ("/caja/turnos/", "fecha_desde", "2026-02-30"),
        ("/caja/turnos/", "fecha_hasta", "9999-12-31"),
        ("/caja/turnos/", "page", "999"),
    ]:
        r_bad = c_adm.get(route, {param: bad})
        d11_results[f"{route}?{param}={bad!r}"] = {
            "status": r_bad.status_code,
            "has_invalid": bool(r_bad.context and r_bad.context.get("has_invalid_query")),
        }
    dup_resp = c_adm.get("/caja/turnos/?fecha_desde=2026-11-14&fecha_desde=2026-11-15")
    d11_results["/caja/turnos/?dup_fecha_desde"] = {
        "status": dup_resp.status_code,
        "has_invalid": bool(dup_resp.context and dup_resp.context.get("has_invalid_query")),
    }
    check("D11-NO-500-HISTORIES", all(v["status"] == 200 and v["has_invalid"] for v in d11_results.values()), d11_results)

    # 4. Cross-role access checks on consulted routes + /admin/login/ check
    c_wh = Client()
    c_wh.login(email=creds["ALMACENERO"]["email"], password=creds["ALMACENERO"]["password"])
    c_sel1 = Client()
    c_sel1.login(email=creds["VENDEDOR"]["email"], password=creds["VENDEDOR"]["password"])
    c_sel2 = Client()
    c_sel2.login(email=creds["VENDEDOR2"]["email"], password=creds["VENDEDOR2"]["password"])

    perms = {
        "wh_stock": c_wh.get("/inventario/stock/").status_code,
        "wh_exp": c_wh.get("/productos/vencimientos/").status_code,
        "wh_sales_hist": c_wh.get("/ventas/historial/").status_code,
        "wh_cash_hist": c_wh.get("/caja/turnos/").status_code,
        "sel1_stock": c_sel1.get("/inventario/stock/").status_code,
        "sel1_exp": c_sel1.get("/productos/vencimientos/").status_code,
        "sel1_prod": c_sel1.get("/productos/").status_code,
        "sel1_sales_hist": c_sel1.get("/ventas/historial/").status_code,
        "sel1_cash_hist": c_sel1.get("/caja/turnos/").status_code,
        "sel1_shift_sales": c_sel1.get("/ventas/turno/").status_code,
        "adm_shift_sales": c_adm.get("/ventas/turno/").status_code,
    }
    check("ROLE-MATRIX", perms == {
        "wh_stock": 200, "wh_exp": 200, "wh_sales_hist": 403, "wh_cash_hist": 403,
        "sel1_stock": 403, "sel1_exp": 403, "sel1_prod": 403,
        "sel1_sales_hist": 200, "sel1_cash_hist": 200, "sel1_shift_sales": 200,
        "adm_shift_sales": 403,
    }, perms)

    # Own-only filter check for VENDEDOR1 vs VENDEDOR2
    s1_vh = c_sel1.get("/ventas/historial/")
    s2_vh = c_sel2.get("/ventas/historial/")
    s1_ch = c_sel1.get("/caja/turnos/")
    s2_ch = c_sel2.get("/caja/turnos/")
    check("OWN-ONLY-SELLER-HISTORIES", (
        {s.correlative for s in s1_vh.context["sales"]} == {"V-13R00001", "V-13R00002"}
        and {s.correlative for s in s2_vh.context["sales"]} == {"V-13R00003", "V-13R00004"}
        and all(sh.seller_id == s1_ch.wsgi_request.user.id for sh in s1_ch.context["shifts"])
        and len(list(s1_ch.context["shifts"])) == 1
        and all(sh.seller_id == s2_ch.wsgi_request.user.id for sh in s2_ch.context["shifts"])
        and len(list(s2_ch.context["shifts"])) == 1
    ), {
        "s1_sales": list(s1_vh.context["sales"].values_list("correlative", flat=True)),
        "s2_sales": list(s2_vh.context["sales"].values_list("correlative", flat=True)),
        "s1_shifts": len(list(s1_ch.context["shifts"])),
        "s2_shifts": len(list(s2_ch.context["shifts"])),
    })

    # Cache-Control contrast on /productos/ (catalog route linked/sibling from stock/dashboard)
    r_prods = c_adm.get("/productos/")
    catalog_cache_control = r_prods.get("Cache-Control", "")

    # 5. Future HUs non-fabrication & 404 ghost routes
    adm_dash_html = c_adm.get("/inicio/").content.decode("utf-8")
    forbidden_future_terms = ["Esta semana", "Este mes", "Ticket promedio", "Yape", "Top 5", "Margen de ganancia", "Solicitudes de reposición"]
    present_future_terms = [t for t in forbidden_future_terms if t.lower() in adm_dash_html.lower()]
    ghost_routes = {path: c_adm.get(path).status_code for path in ["/reportes/", "/tablero/", "/configuracion/", "/exportar/", "/metricas/"]}
    check("NO-FUTURE-FABRICATION", len(present_future_terms) == 0 and all(v == 404 for v in ghost_routes.values()), {
        "leaked_terms": present_future_terms, "ghost_routes": ghost_routes,
    })

    # 6. Fault 500 + Recovery (without false zero or error leak)
    c_adm.raise_request_exception = False
    (run_dir / "force_500_once.flag").write_text("1", encoding="utf-8")
    r500 = c_adm.get("/inicio/")
    h500 = r500.content.decode("utf-8")
    r_rec = c_adm.get("/inicio/")
    h_rec = r_rec.content.decode("utf-8")
    check("FAULT-500-AND-RECOVERY", (
        r500.status_code == 500
        and "No se pudo completar la solicitud" in h500
        and "Volver al inicio" in h500
        and "S/ 0,00" not in h500
        and "SECRET-999" not in h500
        and r_rec.status_code == 200
        and "S/ 1239,99" in h_rec
    ), {
        "r500_status": r500.status_code,
        "r500_x_request_id_header": r500.get("X-Request-ID", ""),
        "r500_body_mentions_request_id": ("request_id" in h500.lower() or r500.get("X-Request-ID", "NONE") in h500),
        "recovered_status": r_rec.status_code,
    })

    # 7. Truly empty DB check via separate SQLite file inside the same run_dir? Use clean sub-process for clean DB
    empty_script = SOPORTE / "audit13_reval.py"
    import subprocess
    empty_run_dir = make_run_dir("etapa13-reval-empty-")
    p_empty = subprocess.run(
        [str(R1 / ".venv" / "Scripts" / "python.exe"), str(empty_script), "--empty-only", str(empty_run_dir)],
        capture_output=True, text=True, check=False,
    )
    empty_data = json.loads(p_empty.stdout) if p_empty.returncode == 0 else {"error": p_empty.stderr}
    check("EMPTY-DB-ZEROES", p_empty.returncode == 0 and empty_data.get("all_ok") is True, empty_data)

    protected_after = sha256_file(protected_db)
    check("PROTECTED-SQLITE-INTACT", protected_before == protected_after, {"before": protected_before, "after": protected_after})

    summary = {
        "run_dir": str(run_dir.relative_to(ROOT)),
        "empty_run_dir": str(empty_run_dir.relative_to(ROOT)),
        "total_checks": len(checks),
        "passed": sum(1 for c in checks if c["ok"]),
        "failed": [c for c in checks if not c["ok"]],
        "checks": checks,
        "role_cards": role_cards,
        "d11_results": d11_results,
        "catalog_productos_cache_control": catalog_cache_control,
        "fixture": fixture,
    }
    (EVID / "server-probes.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"passed": summary["passed"], "total": summary["total_checks"], "failed": len(summary["failed"])}))
    return summary


def run_empty_only(run_dir: Path) -> None:
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.test import Client
    from identity.models import Role

    boot_django(run_dir)
    call_command("migrate", verbosity=0)
    User = get_user_model()
    r_adm, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
    creds = {}
    for k, em, nm, rl in [("ADMIN", "e_adm@test.invalid", "Adm E", r_adm), ("ALMACENERO", "e_wh@test.invalid", "Wh E", r_wh), ("VENDEDOR", "e_sel@test.invalid", "Sel E", r_sel)]:
        pw = "P@ss-" + secrets.token_urlsafe(12)
        User.objects.create_user(email=em, password=pw, display_name=nm, role=rl)
        creds[k] = {"email": em, "password": pw}
    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    c_adm = Client()
    c_adm.login(**creds["ADMIN"])
    adm_html = c_adm.get("/inicio/").content.decode("utf-8")
    cards_adm = extract_cards(adm_html)
    r_stk = c_adm.get("/inventario/stock/")
    r_exp = c_adm.get("/productos/vencimientos/")
    r_vh = c_adm.get("/ventas/historial/")
    r_ch = c_adm.get("/caja/turnos/")

    c_wh = Client()
    c_wh.login(**creds["ALMACENERO"])
    cards_wh = extract_cards(c_wh.get("/inicio/").content.decode("utf-8"))

    c_sel = Client()
    c_sel.login(**creds["VENDEDOR"])
    cards_sel = extract_cards(c_sel.get("/inicio/").content.decode("utf-8"))
    r_sh_sel = c_sel.get("/ventas/turno/")

    ok = (
        cards_adm.get("Ventas de hoy") == "0"
        and cards_adm.get("Total vendido hoy") == "S/ 0,00"
        and cards_adm.get("Descuentos aplicados hoy") == "S/ 0,00"
        and cards_adm.get("Turnos abiertos ahora") == "0"
        and cards_adm.get("Stock en nivel crítico") == "0"
        and cards_adm.get("Lotes por vencer (30 días)") == "0"
        and cards_adm.get("Lotes vencidos con stock") == "0"
        and len(cards_wh) == 3
        and len(cards_sel) == 0
        and all(r.status_code == 200 for r in (r_stk, r_exp, r_vh, r_ch, r_sh_sel))
    )
    print(json.dumps({"all_ok": ok, "cards_adm": cards_adm, "cards_wh": cards_wh, "statuses": [r_stk.status_code, r_exp.status_code, r_vh.status_code, r_ch.status_code, r_sh_sel.status_code]}))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--empty-only":
        run_empty_only(Path(sys.argv[2]))
    else:
        run_probes()
