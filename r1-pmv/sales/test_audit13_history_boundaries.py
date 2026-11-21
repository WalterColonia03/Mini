"""Regression for the dashboard's history destination; not all sales flows."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.utils import timezone

from cash.models import CashRegister, CashShift
from identity.models import Account, Role
from sales.models import Sale


class DashboardHistoryBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin_role, _ = Role.objects.get_or_create(code='ADMIN', defaults={'name': 'Administrador'})
        seller_role, _ = Role.objects.get_or_create(code='VENDEDOR', defaults={'name': 'Vendedor'})
        cls.admin = Account.objects.create_user('history13@test.invalid', role=admin_role, display_name='Admin13')
        seller = Account.objects.create_user('seller13@test.invalid', role=seller_role, display_name='Seller13')
        register = CashRegister.objects.create(code='AUDIT13')
        shift = CashShift.objects.create(cash_register=register, seller=seller, opening_amount=Decimal('0.00'))
        cls.day = timezone.localdate()
        start = timezone.make_aware(datetime.combine(cls.day, time.min))
        for index, at in enumerate([start - timedelta(microseconds=1), start, start + timedelta(days=1) - timedelta(microseconds=1), start + timedelta(days=1)]):
            sale = Sale.objects.create(cash_shift=shift, seller=seller, total_amount=Decimal('3.55'), base_amount=Decimal('3.55'), igv_amount=0, discount_amount=0, cash_received=Decimal('10.00'), change_given=Decimal('6.45'), correlative=f'V-0013000{index}', idempotency_key=uuid4())
            Sale.objects.filter(pk=sale.pk).update(confirmed_at=at)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_invalid_calendar_and_date_range_limits_return_errors_without_rows(self):
        for field, text in [('fecha', 'La fecha ingresada'), ('fecha_desde', 'La fecha inicial ingresada'), ('fecha_hasta', 'La fecha final ingresada')]:
            values = ['2026-02-30', '2026-13-01', '0000-01-01', '20260101', '2026-W01-1', '9' * 5000]
            if field != 'fecha_desde':
                values.append('9999-12-31')
            for value in values:
                with self.subTest(field=field, value=value[:16]):
                    response = self.client.get('/ventas/historial/', {field: value})
                    self.assertContains(response, text)
                    self.assertEqual(list(response.context['sales']), [])
                    self.assertNotContains(response, 'V-00130000')
        self.assertEqual(Sale.objects.count(), 4)

    def test_exact_and_range_filters_preserve_lima_day_boundaries(self):
        for params in [{'fecha': str(self.day)}, {'fecha_desde': str(self.day), 'fecha_hasta': str(self.day)}]:
            with self.subTest(params=params):
                response = self.client.get('/ventas/historial/', params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.context['sales'].values_list('correlative', flat=True)), {'V-00130001', 'V-00130002'})
                self.assertEqual(response.context['total_vendido'], Decimal('7.10'))

    @override_settings(DEBUG=False)
    def test_dashboard_failure_has_no_false_zero_and_next_request_recovers(self):
        self.client.raise_request_exception = False
        with patch('identity.views._dashboard_summary', side_effect=DatabaseError('private diagnostic')):
            response = self.client.get('/inicio/')
        self.assertContains(response, 'No se pudo completar la solicitud', status_code=500)
        self.assertContains(response, 'actualiza la página', status_code=500)
        self.assertNotContains(response, 'S/ 0,00', status_code=500)
        self.assertNotContains(response, 'private diagnostic', status_code=500)
        recovered = self.client.get('/inicio/')
        self.assertEqual(recovered.status_code, 200)
        self.assertEqual(recovered.context['summary']['sales_total'], Decimal('7.10'))
        self.assertEqual(Sale.objects.count(), 4)
