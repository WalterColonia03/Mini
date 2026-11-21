from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
from django.utils import timezone
from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.services import LotInput, confirm_initial_load, register_stock_entry
from sales.models import SaleLine
from sales.services import add_product_to_draft, checkout_sale
from audit03l_concurrency import contest


def run_cases():
    cases = []
    seller_role, _ = Role.objects.get_or_create(code='VENDEDOR', defaults={'name': 'Seller'})
    warehouse_role, _ = Role.objects.get_or_create(code='ALMACENERO', defaults={'name': 'Warehouse'})
    future = timezone.localdate() + timedelta(days=30)
    for first in ['entry', 'sale']:
        seller = Account.objects.create_user(first+'@seller.invalid', None, display_name="Vendedor ficticio", role=seller_role)
        worker = Account.objects.create_user(first+'@worker.invalid', None, display_name="Almacen ficticio", role=warehouse_role)
        CashShift.objects.create(cash_register=CashRegister.objects.create(code=first),
                                 seller=seller, opening_amount=Decimal('50'))
        product = Product.objects.create(category=Category.objects.create(name=first),
                                         name=first, barcode=first, sale_price=Decimal('9'))
        confirm_initial_load(actor=worker, product=product,
                             lots=[LotInput('A',10,Decimal('2'),future),
                                   LotInput('B',10,Decimal('4'),future+timedelta(days=1))])
        draft = add_product_to_draft(actor=seller, product_id=product.pk, quantity=2)
        sale = lambda: str(checkout_sale(actor=seller, draft_id=draft.pk,
                           cash_received=Decimal('20'), idempotency_key=uuid4()).pk)
        entry = lambda: str(register_stock_entry(actor=worker, product=product,
                            lots=[LotInput('C',10,Decimal('6'),future)]).pk)
        race = contest(entry, sale) if first == 'entry' else contest(sale, entry)
        product.refresh_from_db()
        cost = SaleLine.objects.get(product=product).unit_cost
        checks = {
            'lock_observed': race['lock_observed'] and race['distinct_connections'],
            'both_committed': all(race[k]['status']=='committed' for k in ['winner','contender']),
            'sale_snapshot': cost == Decimal('4.0000' if first=='entry' else '3.0000'),
            'average': product.average_cost == Decimal('4.0000' if first=='entry' else '4.0714'),
            'stock': sum(product.lots.values_list('available_quantity',flat=True)) == 28,
        }
        cases.append({'id':'PG-AG-'+first+'-first','ok':all(checks.values()),'checks':checks,'race':race})
    # Migration on this disposable PostgreSQL DB: simulate pre-0005 sales,
    # retain every old column, then verify no fabricated cost on upgrade.
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connection)
    executor.migrate([('sales','0004_saleline_product')])
    with connection.cursor() as c:
        c.execute('SELECT * FROM sales_saleline ORDER BY id')
        before = c.fetchall()
    MigrationExecutor(connection).migrate([('sales','0005_saleline_unit_cost')])
    with connection.cursor() as c:
        c.execute('SELECT * FROM sales_saleline ORDER BY id')
        after = c.fetchall()
    checks = {'old_columns_preserved':[row[:-1] for row in after]==before,
              'legacy_unknown':all(row[-1] is None for row in after), 'two_sales':len(after)==2}
    cases.append({'id':'PG-AG-migration','ok':all(checks.values()),'checks':checks})
    return cases

