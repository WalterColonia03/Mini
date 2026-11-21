from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from identity.models import Account, Role
from identity.services import deactivate_employee, reactivate_employee
from inventory.models import Supplier


class SupplierSessionRevocationTests(TestCase):
    def setUp(self):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        self.admin = Account.objects.create_user("admin04d@test.invalid", "Test-only-04D!", role=role, display_name="Admin aislado")
        self.operator = Account.objects.create_user("operator04d@test.invalid", "Test-only-04D!", role=role, display_name="Operador aislado")

    def test_surviving_identity_is_removed_and_cannot_revive(self):
        supplier = Supplier.objects.create(name="Proveedor aislado", ruc="00123456789")
        for method, url, data in [
            ("get", "/inventario/proveedores/", {}),
            ("get", "/inventario/proveedores/nuevo/", {}),
            ("post", "/inventario/proveedores/nuevo/", {"name": "No guardar", "ruc": "00123456788"}),
            ("post", f"/inventario/proveedores/{supplier.pk}/estado/", {"is_active": "false"}),
            ("get", "/", {}), ("get", "/inicio/", {}),
        ]:
            with self.subTest(method=method, url=url):
                Account.objects.filter(pk=self.admin.pk).update(is_active=True)
                client = Client()
                client.force_login(self.admin)
                key = client.cookies[settings.SESSION_COOKIE_NAME].value
                before = list(Supplier.objects.values())
                Account.objects.filter(pk=self.admin.pk).update(is_active=False)
                response = getattr(client, method)(url, data)
                self.assertEqual(response.status_code, 200 if url == "/" else 302)
                self.assertFalse(Session.objects.filter(session_key=key).exists())
                self.assertEqual(list(Supplier.objects.values()), before)
                Account.objects.filter(pk=self.admin.pk).update(is_active=True)
                replay = Client()
                replay.cookies[settings.SESSION_COOKIE_NAME] = key
                self.assertEqual(replay.get("/inventario/proveedores/").status_code, 302)

    def test_normal_deactivation_revokes_even_without_intermediate_request(self):
        self.client.force_login(self.admin)
        key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        deactivate_employee(actor=self.operator, account=self.admin)
        self.assertFalse(Session.objects.filter(session_key=key).exists())
        reactivate_employee(actor=self.operator, account=self.admin)
        self.assertEqual(self.client.get("/inventario/proveedores/").status_code, 302)

    def test_anonymous_session_without_identity_is_preserved(self):
        session = self.client.session
        session["unrelated"] = "preserved"
        session.save()
        self.client.get("/")
        self.assertEqual(self.client.session["unrelated"], "preserved")
