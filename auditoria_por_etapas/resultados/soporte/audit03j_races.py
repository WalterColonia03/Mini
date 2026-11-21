"""Exercise competing category confirmations through the Django views on an isolated database."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import Client
from django.urls import reverse

from catalog.models import Category, Product
from identity.models import Account, Role


def category_races():
    role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"name": "Administrador"})
    users = [Account.objects.create_user(f"race{i}@test.invalid", None, role=role, display_name=f"ADMIN {i}").pk
             for i in (1, 2)]
    category = Category.objects.create(name="Categoría simultánea")
    product = Product.objects.create(category=category, name="Producto simultáneo", barcode="J-RACE", sale_price="8.50")
    original = Product.objects.values().get(pk=product.pk)
    url = reverse("category-toggle", args=[category.pk])
    cases = []

    def race(label, submissions, expected_state, expected_version):
        barrier = Barrier(2, timeout=10)

        def submit(item):
            close_old_connections()
            user_id, (target, version) = item
            reached = False
            def synchronize(execute, sql, params, many, context):
                nonlocal reached
                if not reached and sql.lstrip().startswith('UPDATE "catalog_category"'):
                    reached = True
                    barrier.wait()
                return execute(sql, params, many, context)
            try:
                client = Client(raise_request_exception=False)
                client.force_login(Account.objects.get(pk=user_id))
                with connection.execute_wrapper(synchronize):
                    response = client.post(url, {"is_active": target, "state_version": str(version), "confirm": "yes"})
                return {"status": response.status_code, "at_write": reached}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, zip(users, submissions)))
        category.refresh_from_db()
        ok = sorted(r["status"] for r in results) == [302, 409] and all(r["at_write"] for r in results)
        ok = ok and category.is_active == expected_state and category.state_version == expected_version
        ok = ok and Product.objects.values().get(pk=product.pk) == original
        cases.append({"id": label, "ok": ok, "responses": results, "active": category.is_active, "version": category.state_version})

    race("J-R1-same-disabling-intent", [("false", 0), ("false", 0)], False, 1)
    race("J-R2-opposite-intents", [("true", 1), ("false", 0)], True, 2)
    race("J-R3-stale-after-state-cycle", [("true", 1), ("false", 2)], False, 3)
    return cases
