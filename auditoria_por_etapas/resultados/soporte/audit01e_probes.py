"""Characterization probes: passing probes may demonstrate an open defect."""
import secrets
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from identity.models import Account, Role, LoginAttempt
from identity.services import authenticate_active_account

class SeparateSurfaceProbes(TestCase):
    def test_distinct_unknown_identifiers_accumulate_and_are_not_globally_throttled(self):
        before = LoginAttempt.objects.count()
        for i in range(12):
            response = self.client.post('/', {'email':f'unknown{i}@probe.invalid','password':secrets.token_urlsafe(12)})
            self.assertEqual(response.status_code,200)
        self.assertEqual(LoginAttempt.objects.count(),before+12)
        self.assertEqual(LoginAttempt.objects.filter(failures=1).count(),12)

    def test_expired_rows_are_retained_after_success(self):
        role = Role.objects.create(code='ADMIN',name='Administrador')
        password = secrets.token_urlsafe(24)
        account = Account.objects.create_user('retained@probe.invalid',password,display_name='Probe',role=role)
        authenticate_active_account(account.email,'incorrect')
        LoginAttempt.objects.update(failures=5,locked_until=timezone.now()-timedelta(days=60))
        self.assertTrue(authenticate_active_account(account.email,password).authenticated)
        self.assertEqual(LoginAttempt.objects.count(),1)
        self.assertEqual(LoginAttempt.objects.get().failures,0)

    def test_staff_and_superuser_bypass_public_lock_with_admin_and_reach_dashboard(self):
        role = Role.objects.create(code='ADMIN',name='Administrador')
        for superuser in (False,True):
            password = secrets.token_urlsafe(24)
            account = Account.objects.create_user(f'maint{int(superuser)}@probe.invalid',password,
                display_name='Maintenance fixture',role=role,is_staff=True,is_superuser=superuser)
            for _ in range(5): authenticate_active_account(account.email,'incorrect')
            self.assertFalse(authenticate_active_account(account.email,password).authenticated)
            client = Client()
            response = client.post('/admin/login/?next=/admin/',
                {'username':account.email,'password':password,'next':'/admin/'})
            self.assertEqual(response.status_code,302)
            self.assertEqual(client.get('/inicio/').status_code,200)
            model_response = client.get('/admin/identity/account/')
            self.assertEqual(model_response.status_code,200 if superuser else 403)
