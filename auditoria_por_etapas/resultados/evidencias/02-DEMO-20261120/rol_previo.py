from django.test import Client
from django.urls import reverse
from identity.test_etapa02_audit import Stage02AuditRegressionTests
from cash.models import CashShift

class RoleAccess(Stage02AuditRegressionTests):
    def test_two_existing_sessions(self):
        sessions = [Client(), Client()]
        for session in sessions:
            session.force_login(self.seller2)
            self.assertEqual(session.get(reverse("cash-open")).status_code, 200)
        self.client.force_login(self.admin)
        result = self.client.post(reverse("employee-edit", args=[self.seller2.pk]), {
            "display_name": self.seller2.display_name, "email": self.seller2.email,
            "role": self.warehouse_role.pk, "new_password": "",
        })
        self.assertEqual(result.status_code, 302)
        self.seller2.refresh_from_db()
        self.assertEqual(self.seller2.role_id, self.warehouse_role.pk)
        for session in sessions:
            self.assertEqual(session.get(reverse("cash-open")).status_code, 403)
        self.assertFalse(CashShift.objects.filter(seller=self.seller2).exists())
