"""Panel minimum: snapshot statement, role separation, empty and boundary data."""
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from catalog.models import Category, Product
from inventory.models import InitialInventoryLoad, Lot
from identity.models import Account, Role
from identity.views import _dashboard_summary


class DashboardSummaryTests(TestCase):
    def test_empty_summary_is_one_statement_with_decimal_money(self):
        with self.assertNumQueries(1):
            summary = _dashboard_summary(Role.Code.ADMIN, timezone.localdate())
        self.assertEqual(summary, dict(expiring=0, expired=0, low_stock=0, sales_count=0,
                                       sales_total=Decimal('0'), discount_total=Decimal('0'), open_shifts=0))
        self.assertIsInstance(summary['sales_total'], Decimal)
        self.assertIsInstance(summary['discount_total'], Decimal)

    def test_roles_do_not_query_financial_tables_without_authorization(self):
        with CaptureQueriesContext(connection) as queries:
            summary = _dashboard_summary(Role.Code.WAREHOUSE, timezone.localdate())
        self.assertEqual(len(queries), 1)
        self.assertEqual(set(summary), {'expiring', 'expired', 'low_stock'})
        self.assertNotIn('sales_sale', queries[0]['sql'])
        self.assertNotIn('cash_cashshift', queries[0]['sql'])
        with self.assertNumQueries(0):
            self.assertIsNone(_dashboard_summary(Role.Code.SELLER, timezone.localdate()))
            self.assertIsNone(_dashboard_summary('INVALID', timezone.localdate()))

    def test_equality_inactive_physical_stock_and_day_boundaries(self):
        role = Role.objects.create(code=Role.Code.WAREHOUSE, name='Almacenero')
        actor = Account.objects.create_user('summary13@test.invalid', display_name='Almacén', role=role)
        category = Category.objects.create(name='Summary13')
        day = timezone.localdate()
        for index, (active, minimum, lots) in enumerate([
            (True, 5, [(1, 2), (30, 3)]),  # equality is critical
            (True, 0, []),                # empty sellable stock counts
            (False, 99, [(0, 7), (30, 4)]), # physical alerts remain, no critical
            (True, 0, [(31, 2), (30, 0)]), # outside window and zero lot excluded
        ]):
            product = Product.objects.create(category=category, name=f'Summary {index}',
                                             barcode=f'SUM13-{index}', sale_price=Decimal('3.55'),
                                             is_active=active, minimum_stock=minimum)
            load = InitialInventoryLoad.objects.create(product=product, responsible=actor)
            for number, (days, qty) in enumerate(lots):
                Lot.objects.create(product=product, initial_load=load, responsible=actor,
                                   number=f'SUM-{number}', initial_quantity=max(1, qty),
                                   available_quantity=qty, unit_cost=Decimal('1.2345'),
                                   expiration_date=day+timedelta(days=days))
        with self.assertNumQueries(1):
            summary = _dashboard_summary(Role.Code.WAREHOUSE, day)
        self.assertEqual(summary, dict(expiring=3, expired=1, low_stock=2))
