"""Security regression: a stale state form must never reverse the requested action."""
from django.test import Client, TestCase
from django.urls import reverse

from identity.models import Account, Role


class EmployeeStateIntentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        cls.seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
        cls.admin = Account.objects.create_user("admin-state@example.invalid", "Testpass12!", display_name="Admin ficticio", role=cls.admin_role)
        cls.seller = Account.objects.create_user("seller-state@example.invalid", "Testpass12!", display_name="Vendedor ficticio", role=cls.seller_role)

    def test_stale_deactivate_form_never_reactivates_employee(self):
        first, second = Client(), Client()
        first.force_login(self.admin)
        second.force_login(self.admin)
        first.get(reverse("employee-list"))
        second.get(reverse("employee-list"))
        url = reverse("employee-deactivate", args=[self.seller.pk])
        self.assertEqual(first.post(url, {"action": "desactivar"}).status_code, 302)
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_active)
        self.assertEqual(second.post(url, {"action": "desactivar"}).status_code, 302)
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_active, "Un formulario antiguo de desactivación reactivó la cuenta")

    def test_explicit_reactivation_and_replay_do_not_deactivate(self):
        self.client.force_login(self.admin)
        url = reverse("employee-deactivate", args=[self.seller.pk])
        self.client.post(url, {"action": "desactivar"})
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_active)
        for _ in range(2):
            self.assertEqual(self.client.post(url, {"action": "reactivar"}).status_code, 302)
            self.seller.refresh_from_db()
            self.assertTrue(self.seller.is_active)

    def test_missing_invalid_or_ambiguous_action_rejected_without_state_change(self):
        self.client.force_login(self.admin)
        url = reverse("employee-deactivate", args=[self.seller.pk])
        for data in ({}, {"action": ""}, {"action": "otro"}, {"action": ["desactivar", "reactivar"]}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post(url, data).status_code, 400)
                self.seller.refresh_from_db()
                self.assertTrue(self.seller.is_active)

    def test_non_admin_cannot_submit_state_change(self):
        self.client.force_login(self.seller)
        response = self.client.post(reverse("employee-deactivate", args=[self.admin.pk]), {"action": "desactivar"})
        self.assertEqual(response.status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_missing_csrf_cannot_submit_state_change(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(reverse("employee-deactivate", args=[self.seller.pk]), {"action": "desactivar"})
        self.assertEqual(response.status_code, 403)
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.is_active)

    def test_list_sends_intended_action_and_self_has_no_state_button(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("employee-list"))
        self.assertContains(response, 'name="action" value="desactivar"')
        self.assertNotContains(response, reverse("employee-deactivate", args=[self.admin.pk]))
        self.seller.is_active = False
        self.seller.save(update_fields=["is_active"])
        response = self.client.get(reverse("employee-list"))
        self.assertContains(response, 'name="action" value="reactivar"')
