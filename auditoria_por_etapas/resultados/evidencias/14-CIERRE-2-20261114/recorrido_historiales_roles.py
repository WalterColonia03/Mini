"""Chrome real: historiales estables (25/pág), borrador/reclasificación, salida y aislamiento."""
import argparse
import importlib.util
import json
import uuid
from decimal import Decimal
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("base14", HERE.parent / "14-D-20261113/navegador/recorrido.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
original_prepare = base.prepare
FIXTURE = {}


def prepare(db, password):
    original_prepare(db, password)
    from django.db import connection
    from django.utils import timezone
    from cash.models import CashRegister, CashShift, CashShiftClose
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import Sale, SaleLine

    admin = Account.objects.get(email="admin@example.invalid")
    warehouse = Account.objects.get(email="almacenero@example.invalid")
    seller_a = Account.objects.get(email="vendedor@example.invalid")
    seller_role = Role.objects.get(code=Role.Code.SELLER)
    seller_b = Account.objects.create_user(
        email="vendedor2@example.invalid",
        password=password,
        display_name="Vendedor Dos 14C2",
        role=seller_role,
        is_active=True,
    )
    reg = CashRegister.objects.get(code="CAJA-01")

    cat_a = Category.objects.create(name="Lacteos 14C2", is_active=True)
    cat_b = Category.objects.create(name="Bebidas 14C2", is_active=True)

    p_reclas = Product.objects.create(
        name="Yogurt Reclas 14C2",
        barcode="INT-REC-14C2",
        barcode_type="INTERNAL",
        barcode_normalized="INT-REC-14C2",
        search_name="yogurt reclas 14c2",
        category=cat_a,
        unit="UND",
        sale_price=Decimal("7.50"),
        minimum_stock=1,
        controls_expiration=True,
    )
    confirm_initial_load(
        actor=warehouse,
        product=p_reclas,
        lots=[LotInput("L-REC-1", 10, Decimal("4.00"), timezone.localdate() + timedelta(days=45))],
    )

    p_draft = Product.objects.create(
        name="Gaseosa Borrador 14C2",
        barcode="INT-DRF-14C2",
        barcode_type="INTERNAL",
        barcode_normalized="INT-DRF-14C2",
        search_name="gaseosa borrador 14c2",
        category=cat_b,
        unit="UND",
        sale_price=Decimal("4.50"),
        minimum_stock=1,
        controls_expiration=True,
    )
    confirm_initial_load(
        actor=warehouse,
        product=p_draft,
        lots=[LotInput("L-DRF-1", 10, Decimal("2.50"), timezone.localdate() + timedelta(days=60))],
    )

    p_cost = Product.objects.create(
        name="Cafe Privado 14C2",
        barcode="INT-CST-14C2",
        barcode_type="INTERNAL",
        barcode_normalized="INT-CST-14C2",
        search_name="cafe privado 14c2",
        category=cat_a,
        unit="UND",
        sale_price=Decimal("10.00"),
        minimum_stock=1,
        controls_expiration=True,
    )
    confirm_initial_load(
        actor=warehouse,
        product=p_cost,
        lots=[LotInput("L-CST-1", 30, Decimal("4.3333"), timezone.localdate() + timedelta(days=90))],
    )

    # Seed 26 tied closed shifts (14 seller_a + 12 seller_b) and 26 tied sales for deterministic 25/page pagination
    same_ts = timezone.now()
    closed_shifts_a = []
    closed_shifts_b = []
    for idx in range(26):
        owner = seller_a if idx < 14 else seller_b
        sh = CashShift.objects.create(
            cash_register=reg,
            seller=owner,
            opening_amount=Decimal(f"{100 + idx}.00"),
            status=CashShift.Status.CLOSED,
        )
        CashShift.objects.filter(pk=sh.pk).update(opened_at=same_ts)
        CashShiftClose.objects.create(
            cash_shift=sh,
            counted_amount=Decimal(f"{110 + idx}.00"),
            expected_amount=Decimal(f"{110 + idx}.00"),
            difference=Decimal("0.00"),
            closed_by=owner,
        )
        (closed_shifts_a if idx < 14 else closed_shifts_b).append(sh)

    sales_list = []
    for idx in range(26):
        if idx < 14:
            owner, sh = seller_a, closed_shifts_a[idx]
        else:
            owner, sh = seller_b, closed_shifts_b[idx - 14]
        sale = Sale.objects.create(
            cash_shift=sh,
            seller=owner,
            seller_snapshot_name=owner.display_name,
            cash_register_snapshot_code=reg.code,
            total_amount=Decimal("10.00"),
            base_amount=Decimal("8.47"),
            igv_amount=Decimal("1.53"),
            discount_amount=Decimal("0.00"),
            cash_received=Decimal("10.00"),
            change_given=Decimal("0.00"),
            correlative=f"V-{idx + 1:08d}",
            idempotency_key=uuid.uuid4(),
        )
        Sale.objects.filter(pk=sale.pk).update(confirmed_at=same_ts)
        SaleLine.objects.create(
            sale=sale,
            position=1,
            product=p_cost,
            product_snapshot_name=p_cost.name,
            product_snapshot_barcode=p_cost.barcode,
            quantity=1,
            unit_price=Decimal("10.00"),
            amount=Decimal("10.00"),
            unit_cost=Decimal("4.3333"),
        )
        sales_list.append((sale, owner.pk))

    # Also update SaleCounter to avoid correlative collision on subsequent UI sales
    from sales.models import SaleCounter
    SaleCounter.objects.update_or_create(id=1, defaults={"next_value": 27})

    foreign_shift = closed_shifts_b[0]
    foreign_sale = next(s for s, owner_pk in sales_list if owner_pk == seller_b.pk)
    own_sale = next(s for s, owner_pk in sales_list if owner_pk == seller_a.pk)

    FIXTURE.update(
        today=timezone.localdate().isoformat(),
        seller_a_id=str(seller_a.pk),
        seller_b_id=str(seller_b.pk),
        seller_b_email=seller_b.email,
        cat_b_id=str(cat_b.pk),
        p_reclas_id=str(p_reclas.pk),
        p_draft_id=str(p_draft.pk),
        foreign_shift_id=str(foreign_shift.pk),
        foreign_sale_id=str(foreign_sale.pk),
        own_sale_id=str(own_sale.pk),
    )
    connection.close()


class Journey(base.Journey):
    def login_email(self, browser, email, password):
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(self.base + "/")
        page.locator('[name="email"]').fill(email)
        page.locator('[name="password"]').fill(password)
        page.locator('button[type="submit"]').click()
        page.wait_for_load_state("networkidle")
        return page

    def run(self, browser, password):
        a = self.connect(browser, "ADMIN", password)
        v = self.connect(browser, "VENDEDOR", password)
        vb = self.login_email(browser, FIXTURE["seller_b_email"], password)
        base.save(self.out / "fixture.json", FIXTURE)

        base_witness = base.witness(self.db)

        # HR01: Admin shift history tie-break pagination (25 + 1 = 26, disjoint UUIDs)
        base.link(a, "/caja/turnos/")
        p1_hrefs = a.locator("tbody a[href*='/caja/turnos/']").evaluate_all(
            "els => els.map(e => e.getAttribute('href'))"
        )
        self.observe(
            "HR01-turnos-pagina1",
            "ADMIN",
            a,
            lambda s, t: len(p1_hrefs) == 25 and "26" in a.get_by_test_id("shift-history-summary").inner_text(),
            same=base_witness,
            photo=True,
        )
        a.get_by_role("link", name="Siguiente", exact=True).click()
        p2_hrefs = a.locator("tbody a[href*='/caja/turnos/']").evaluate_all(
            "els => els.map(e => e.getAttribute('href'))"
        )
        assert len(p2_hrefs) == 1 and not (set(p1_hrefs) & set(p2_hrefs))
        self.observe("HR02-turnos-pagina2", "ADMIN", a, same=base_witness, photo=True)

        # HR03: Date overflow/bad filter + preserved filter pagination on cash shifts
        a.goto(self.base + f"/caja/turnos/?fecha_desde={FIXTURE['today']}&fecha_hasta={FIXTURE['today']}")
        next_href = a.get_by_role("link", name="Siguiente", exact=True).get_attribute("href")
        assert f"fecha_desde={FIXTURE['today']}" in next_href and f"fecha_hasta={FIXTURE['today']}" in next_href
        a.goto(self.base + "/caja/turnos/?fecha_hasta=9999-12-31")
        self.observe(
            "HR03-turnos-fecha-overflow",
            "ADMIN",
            a,
            lambda s, t: a.locator(".alert-error").count() > 0 and "No se realizó la consulta" in t,
            same=base_witness,
            photo=True,
        )
        a.goto(self.base + "/caja/turnos/?page=99")
        self.observe(
            "HR04-turnos-pagina-invalida",
            "ADMIN",
            a,
            lambda s, t: a.locator(".alert-error").count() > 0 and "No se realizó la consulta" in t,
            same=base_witness,
        )

        # HR05: Seller A shift isolation & parameter tampering block
        v.goto(self.base + f"/caja/turnos/?vendedor={FIXTURE['seller_b_id']}")
        self.observe(
            "HR05-vendedor-turnos-propios",
            "VENDEDOR",
            v,
            lambda s, t: "14" in v.get_by_test_id("shift-history-summary").inner_text() and "Vendedor Dos" not in v.locator("tbody").inner_text(),
            same=base_witness,
            photo=True,
        )
        resp_foreign_shift = v.request.get(self.base + f"/caja/turnos/{FIXTURE['foreign_shift_id']}/cerrado/")
        assert resp_foreign_shift.status == 404

        # HR06: Admin sales history pagination + full-set total + filter preservation + overflow guard
        base.link(a, "/ventas/historial/")
        s1_rows = a.locator("tbody tr").count()
        self.observe(
            "HR06-ventas-pagina1",
            "ADMIN",
            a,
            lambda s, t: s1_rows == 25 and "260,00" in t and "Total vendido (filtrado):" in t,
            same=base_witness,
            photo=True,
        )
        a.get_by_role("link", name="Siguiente", exact=True).click()
        s2_rows = a.locator("tbody tr").count()
        self.observe(
            "HR07-ventas-pagina2-total-global",
            "ADMIN",
            a,
            lambda s, t: s2_rows == 1 and "260,00" in t,
            same=base_witness,
            photo=True,
        )
        a.goto(self.base + "/ventas/historial/?fecha_hasta=9999-12-31")
        assert a.locator(".alert-error").count() > 0 and "No se realizó la consulta" in a.locator("main").inner_text()

        # HR08: Admin opens receipt -> no "Nueva venta", never purchase unit_cost 4,3333 / 4.3333
        a.goto(self.base + f"/ventas/constancia/{FIXTURE['own_sale_id']}/")
        self.observe(
            "HR08-constancia-admin-sin-costo",
            "ADMIN",
            a,
            lambda s, t: "Nueva venta" not in t and "4,3333" not in t and "4.3333" not in t and "V-00000001" in t,
            same=base_witness,
            photo=True,
        )

        # HR09: Seller navigation links inside sales history & denied foreign routes
        v.goto(self.base + "/ventas/historial/")
        self.observe(
            "HR09-enlaces-vendedor-historial",
            "VENDEDOR",
            v,
            lambda s, t: v.get_by_role("link", name="Ventas del turno", exact=True).count() >= 1
            and v.get_by_role("link", name="Mis turnos", exact=True).count() >= 1,
            same=base_witness,
            photo=True,
        )
        assert v.request.get(self.base + f"/ventas/constancia/{FIXTURE['foreign_sale_id']}/").status == 404
        assert v.request.get(self.base + "/productos/").status == 403

        # HR10: Logout check BEFORE open shift (both Admin and Seller must not claim open shift)
        a.goto(self.base + "/salir/")
        assert "turno abierto" not in a.locator("main").inner_text().lower()
        v.goto(self.base + "/salir/")
        self.observe(
            "HR10-salir-sin-turno",
            "VENDEDOR",
            v,
            lambda s, t: "turno abierto" not in v.locator("main").inner_text().lower(),
            same=base_witness,
            photo=True,
        )

        # HR11: Seller opens shift, groups/updates/removes last draft line (HU-VEN-01b), discards draft
        v.goto(self.base + "/caja/abrir/")
        base.fill(v, "opening_amount", "50.00")
        base.button(v, "Abrir turno")

        v.goto(self.base + "/ventas/")
        base.fill(v, "query", "INT-DRF-14C2")
        base.button(v, "Buscar")
        base.fill(v, "quantity", "2")
        base.button(v, "Agregar")
        base.fill(v, "query", "INT-DRF-14C2")
        base.button(v, "Buscar")
        base.fill(v, "quantity", "3")
        base.button(v, "Agregar")

        line_qty_input = v.locator('form[action^="/ventas/lineas/"]:not([action$="/quitar/"]) input[name="quantity"]').first
        assert line_qty_input.input_value() == "5"
        line_qty_input.fill("4")
        with v.expect_navigation():
            v.locator('form[action^="/ventas/lineas/"]:not([action$="/quitar/"]) button[type="submit"]').first.click()
        assert v.locator('form[action^="/ventas/lineas/"]:not([action$="/quitar/"]) input[name="quantity"]').first.input_value() == "4"
        self.observe("HR11-borrador-agrupado-actualizado", "VENDEDOR", v, photo=True)

        # Removing the last line auto-discards the draft
        with v.expect_navigation():
            v.get_by_role("button", name="Quitar", exact=True).click()
        after_remove = self.observe(
            "HR12-quitar-ultima-linea-descarta",
            "VENDEDOR",
            v,
            lambda s, t: not any(r["status"] == "ACTIVE" for r in s["borrador"]) and s["filas"]["sales_saledraftline"] == 0,
            photo=True,
        )

        # Prepare draft for ProdReclas while Admin reclassifies ProdReclas category (HU-PROD-04/CA-05)
        base.fill(v, "query", "INT-REC-14C2")
        base.button(v, "Buscar")
        base.fill(v, "quantity", "2")
        base.button(v, "Agregar")
        base.link(v, "/ventas/cobrar/")
        before_reclas = self.observe("HR13-borrador-antes-reclasificacion", "VENDEDOR", v, photo=True)

        a.goto(self.base + f"/productos/{FIXTURE['p_reclas_id']}/editar/")
        base.selector(a, "category").select_option(FIXTURE["cat_b_id"])
        base.button(a, "Guardar cambios")
        reclassified = self.observe(
            "HR14-admin-reclasifica-producto",
            "ADMIN",
            a,
            lambda s, t: any(p["id"] == FIXTURE["p_reclas_id"] for p in s["productos"]),
            photo=True,
        )

        # Seller finishes checkout seamlessly after reclassification
        base.fill(v, "cash_received", "20.00")
        base.button(v, "Confirmar cobro")
        sold = self.observe(
            "HR15-cobro-tras-reclasificacion",
            "VENDEDOR",
            v,
            lambda s, t: len(s["ventas"]) == 27 and "V-00000027" in t,
            photo=True,
        )

        # Seller checks "Ventas del turno" (/ventas/historial/turno/)
        v.goto(self.base + "/ventas/historial/turno/")
        self.observe(
            "HR16-ventas-del-turno",
            "VENDEDOR",
            v,
            lambda s, t: "V-00000027" in t and "V-00000001" not in t and v.get_by_role("link", name="Mis turnos", exact=True).count() >= 1,
            same=sold,
            photo=True,
        )

        # Logout safety (HU-AUTH-03): prepare draft, cancel keeps draft, confirm discards draft & keeps open shift
        v.goto(self.base + "/ventas/")
        base.fill(v, "query", "INT-DRF-14C2")
        base.button(v, "Buscar")
        base.fill(v, "quantity", "1")
        base.button(v, "Agregar")
        draft_before_logout = self.observe("HR17-borrador-antes-salir", "VENDEDOR", v)

        v.goto(self.base + "/salir/")
        assert "turno" in v.locator("main").inner_text().lower() and "preparación" in v.locator("main").inner_text().lower()
        with v.expect_navigation():
            v.get_by_role("link", name="Cancelar", exact=True).click()
        self.observe(
            "HR18-salir-cancelado-conserva-borrador",
            "VENDEDOR",
            v,
            lambda s, t: sum(1 for r in s["borrador"] if r["status"] == "ACTIVE" and r["quantity"] == 1) == 1,
            same=draft_before_logout,
        )

        v.goto(self.base + "/salir/")
        base.button(v, "Cerrar sesión")
        after_logout = self.observe(
            "HR19-salir-confirmado-descarta-borrador",
            "VENDEDOR",
            v,
            lambda s, t: (
                not any(r["status"] == "ACTIVE" for r in s["borrador"])
                and s["filas"]["sales_saledraftline"] == 0
                and any(sh["status"] == "OPEN" for sh in s["turnos"])
            ),
            photo=True,
        )
        v.goto(self.base + "/ventas/")
        assert v.url.rstrip("/") == self.base.rstrip("/")

        # Seller B cannot open parallel shift or prepare sales in Seller A's shift
        vb.goto(self.base + "/caja/abrir/")
        self.observe("HR20-vendedor-b-bloqueado", "VENDEDOR_B", vb, lambda s, t: "abrir" not in vb.url or "abierto" in t.lower(), same=after_logout, photo=True)

        # Seller A logs back in, recovers open shift without draft, closes shift cleanly
        v.locator('[name="email"]').fill("vendedor@example.invalid")
        v.locator('[name="password"]').fill(password)
        with v.expect_navigation():
            v.locator('button[type="submit"]').click()
        v.wait_for_load_state("networkidle")
        v.goto(self.base + "/caja/cerrar/")
        base.fill(v, "counted_amount", "65.00")
        base.button(v, "Cerrar turno")
        closed = self.observe(
            "HR21-reingreso-y-cierre-exacto",
            "VENDEDOR",
            v,
            lambda s, t: "Exacto" in t and not any(sh["status"] == "OPEN" for sh in s["turnos"]),
            photo=True,
        )

        # Accessibility keyboard focus + 390x844 mobile viewport overflow check on history pages
        a.goto(self.base + "/caja/turnos/")
        a.locator('.table-responsive[tabindex="0"]').focus()
        assert a.evaluate("document.activeElement.classList.contains('table-responsive')")
        for path, label in [
            ("/caja/turnos/", "HR22-movil-turnos"),
            ("/ventas/historial/", "HR23-movil-ventas"),
        ]:
            a.set_viewport_size({"width": 390, "height": 844})
            a.goto(self.base + path)
            self.observe(label, "ADMIN", a, same=closed, photo=True)
            assert a.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow horizontal en {path}"

        base.save(
            self.out / "resultado.json",
            dict(
                turnos_empatados_paginados=True,
                ventas_empatadas_paginadas_total_global=True,
                filtros_preservados_y_overflow_protegido=True,
                borrador_agrupado_actualizado_y_limpiado=True,
                reclasificacion_con_borrador_abierto=True,
                salida_segura_cancelar_confirmar_y_reingreso=True,
                movil_390_y_foco_teclado_ok=True,
            ),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida", type=Path)
    args = parser.parse_args()
    base.prepare = prepare
    base.Journey = Journey
    base.main(args.salida)
