"""03-K7: competing product edits through the Django views on an isolated, marked SQLite file.

Both requests carry the same opened version and are released together at the first
UPDATE of catalog_product. Expected: one save and one stale rejection, or an idempotent
success when both requests ask for identical values; never a lost update.
"""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import html
import re
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import Client
from django.urls import reverse

from catalog.models import Category, Product
from identity.models import Account, Role

STALE = "El producto cambió desde que abrió esta pantalla."
TOKEN = re.compile(r'name="edit_snapshot" value="([^"]+)"')


def product_races():
    import os
    if os.environ.get("AUDIT03K7_BASELINE") == "read-then-write":
        # Counter-test only: reproduce the first 03-K7 fix (SELECT ... FOR UPDATE, then compare)
        # by disabling the conditional UPDATE. Never used for an approval result.
        import catalog.services as services
        services._lock_unchanged_product = lambda product, snapshot: None
    role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"name": "Administrador"})
    users = [Account.objects.create_user(f"k7race{i}@audit03.invalid", None, role=role,
                                         display_name=f"AUD03 K7 {i}").pk for i in (1, 2)]
    category = Category.objects.create(name="Concurrencia K7")
    cases = []

    def opened(user_id, url):
        client = Client(raise_request_exception=False)
        client.force_login(Account.objects.get(pk=user_id))
        page = client.get(url)
        return client, html.unescape(TOKEN.search(page.content.decode()).group(1))

    def race(label, name, barcode, actors, changes, expected_statuses, acceptable_finals):
        product = Product.objects.create(category=category, name=name, barcode=barcode,
                                         sale_price=Decimal("8.50"), minimum_stock=10)
        url = reverse("product-edit", args=[product.pk])
        base = {"name": name, "barcode": barcode, "category": str(category.pk),
                "sale_price": "8.50", "minimum_stock": "10"}
        sessions = [opened(users[actor], url) for actor in actors]
        connections.close_all()
        barrier = Barrier(2, timeout=10)

        def submit(index):
            close_old_connections()
            client, token = sessions[index]
            reached = False

            def synchronize(execute, sql, params, many, context):
                nonlocal reached
                if not reached and sql.lstrip().startswith('UPDATE "catalog_product"'):
                    reached = True
                    barrier.wait()
                return execute(sql, params, many, context)

            try:
                with connection.execute_wrapper(synchronize):
                    response = client.post(url, {**base, **changes[index], "edit_snapshot": token})
                body = response.content.decode(errors="replace")
                return {"status": response.status_code, "stale_message": STALE in body, "at_write": reached}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, (0, 1)))
        final = Product.objects.values("name", "barcode", "sale_price", "minimum_stock").get(pk=product.pk)
        final["sale_price"] = str(final["sale_price"])
        statuses = sorted((r["status"], r["stale_message"]) for r in results)
        ok = (statuses == sorted(expected_statuses) and all(r["at_write"] for r in results)
              and final in acceptable_finals)
        cases.append({"id": label, "ok": ok, "responses": results, "final": final,
                      "acceptable_finals": acceptable_finals})

    conflict = [(200, True), (302, False)]
    race("K7-R1-two-admins-price-vs-minimum", "K7 carrera precio", "K7R-A", (0, 1),
         [{"sale_price": "9.20"}, {"minimum_stock": "17"}], conflict,
         [{"name": "K7 carrera precio", "barcode": "K7R-A", "sale_price": "9.20", "minimum_stock": 10},
          {"name": "K7 carrera precio", "barcode": "K7R-A", "sale_price": "8.50", "minimum_stock": 17}])
    race("K7-R2-two-admins-code-vs-name", "K7 carrera codigo", "K7R-B", (0, 1),
         [{"barcode": "K7R-CORREGIDO"}, {"name": "K7 carrera nombre"}], conflict,
         [{"name": "K7 carrera codigo", "barcode": "K7R-CORREGIDO", "sale_price": "8.50", "minimum_stock": 10},
          {"name": "K7 carrera nombre", "barcode": "K7R-B", "sale_price": "8.50", "minimum_stock": 10}])
    race("K7-R3-same-admin-double-submit", "K7 doble envio", "K7R-C", (0, 0),
         [{"sale_price": "9.20"}, {"sale_price": "9.20"}], [(302, False), (302, False)],
         [{"name": "K7 doble envio", "barcode": "K7R-C", "sale_price": "9.20", "minimum_stock": 10}])
    return cases
