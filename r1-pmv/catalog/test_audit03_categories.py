"""Stage03-A: category contract, rejected writes and downstream boundaries."""
from decimal import Decimal
from unittest.mock import patch
from importlib import import_module
from types import SimpleNamespace
from datetime import timedelta
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.apps import apps
from django.utils import timezone
from django.test import Client, TestCase
from django.urls import reverse

from identity.models import Account, Role
from catalog.models import Category
from catalog.services import create_category, toggle_category_status


class CategoryAudit03Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actors={}
        for code in ['ADMIN','ALMACENERO','VENDEDOR']:
            role=Role.objects.create(code=code,name=code)
            cls.actors[code]=Account.objects.create_user(code.lower()+'@audit03.invalid',None,display_name='AUD03 '+code,role=role)
        cls.admin=cls.actors['ADMIN']

    def setUp(self):
        self.client.force_login(self.admin)

    def test_empty_list_then_all_names_including_inactive(self):
        self.assertContains(self.client.get(reverse('category-list')),'No hay categorías registradas.')
        Category.objects.create(name='Zeta',is_active=False)
        Category.objects.create(name='Alfa')
        response=self.client.get(reverse('category-list'))
        self.assertEqual([c.name for c in response.context['categories']],['Alfa','Zeta'])
        self.assertContains(response,'Inactiva')

    def test_create_collapses_spaces_and_persists_active(self):
        response=self.client.post(reverse('category-create'),{'name':'  AUD03   Bebidas\t y\u00a0jugos  ','is_active':'false'})
        self.assertRedirects(response,reverse('category-list'))
        category=Category.objects.get()
        self.assertEqual(category.name,'AUD03 Bebidas y jugos')
        self.assertEqual(category.name_normalized,'aud03 bebidas y jugos')
        self.assertTrue(category.is_active)

    def test_duplicate_case_spaces_and_inactive_are_rejected(self):
        Category.objects.create(name='AUD03 Bebidas y jugos',is_active=False)
        for name in ['aud03 bebidas y jugos',' AUD03   Bebidas y jugos ','AUD03\tBEBIDAS Y JUGOS']:
            with self.subTest(name=name):
                response=self.client.post(reverse('category-create'),{'name':name})
                self.assertEqual(response.status_code,200)
                self.assertContains(response,'La categoría ya existe')
                self.assertEqual(Category.objects.count(),1)

    def test_missing_empty_and_whitespace_show_required_error(self):
        for payload in [{},{'name':''},{'name':' \t\u00a0 '}]:
            with self.subTest(payload=payload):
                response=self.client.post(reverse('category-create'),payload)
                self.assertContains(response,'El nombre es obligatorio')
                self.assertEqual(Category.objects.count(),0)

    def test_name_length_120_and_121_and_service_validation(self):
        response=self.client.post(reverse('category-create'),{'name':'A'*120})
        self.assertEqual(response.status_code,302)
        for name in ['B'*121,'ß'*61,'','   ','!!!']:
            with self.subTest(length=len(name)):
                before=Category.objects.count()
                with self.assertRaises(ValidationError): create_category(actor=self.admin,name=name)
                self.assertEqual(Category.objects.count(),before)

    def test_form_rejects_121_and_script_is_escaped(self):
        response=self.client.post(reverse('category-create'),{'name':'B'*121})
        self.assertEqual(response.status_code,200)
        self.assertEqual(Category.objects.count(),0)
        self.client.post(reverse('category-create'),{'name':'<script>AUD03</script>'})
        response=self.client.get(reverse('category-list'))
        self.assertContains(response,'&lt;script&gt;AUD03&lt;/script&gt;')
        self.assertNotContains(response,'<script>AUD03</script>')

    def test_methods_absent_uuid_and_csrf_do_not_mutate(self):
        category=Category.objects.create(name='AUD03 state')
        toggle=reverse('category-toggle',args=[category.pk])
        self.assertEqual(self.client.get(toggle).status_code,405)
        self.assertEqual(self.client.post(reverse('category-list'),{}).status_code,405)
        self.assertEqual(self.client.post(reverse('category-toggle',args=[uuid.uuid4()]),{}).status_code,404)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post(toggle,{}).status_code,403)
        self.assertEqual(csrf.post(reverse('category-create'),{'name':'CSRF'}).status_code,403)
        category.refresh_from_db();self.assertTrue(category.is_active)
        self.assertEqual(Category.objects.count(),1)

    def test_other_roles_and_anonymous_cannot_read_or_write_categories(self):
        category=Category.objects.create(name='AUD03 protected')
        for role in ['ALMACENERO','VENDEDOR',None]:
            c=Client()
            if role: c.force_login(self.actors[role])
            for url in [reverse('category-list'),reverse('category-create'),reverse('category-toggle',args=[category.pk])]:
                for method in ['get','post']:
                    with self.subTest(role=role,url=url,method=method):
                        response=getattr(c,method)(url,{'name':'FORBIDDEN'})
                        self.assertEqual(response.status_code,403 if role else 302)
            category.refresh_from_db();self.assertTrue(category.is_active)
            self.assertEqual(Category.objects.count(),1)

    def test_services_deny_warehouse_and_seller(self):
        category=Category.objects.create(name='AUD03 protected')
        for role in ['ALMACENERO','VENDEDOR']:
            with self.assertRaises(PermissionDenied): create_category(actor=self.actors[role],name='Denied')
            with self.assertRaises(PermissionDenied): toggle_category_status(actor=self.actors[role],category=category)
        self.assertEqual(Category.objects.count(),1)

    def test_duplicate_insert_race_is_a_validation_error(self):
        Category.objects.create(name='AUD03 race')
        # Force the pre-check to miss an existing row; the actual unique index
        # rejects the insert. This exercises recovery, not PG concurrency.
        with patch('django.db.models.query.QuerySet.exists',side_effect=[False,True]):
            with self.assertRaisesMessage(ValidationError,'La categoría ya existe'):
                create_category(actor=self.admin,name='AUD03 race')
        self.assertEqual(Category.objects.count(),1)

    def test_unrelated_database_failure_is_not_hidden(self):
        with patch.object(Category,'save',side_effect=IntegrityError('unrelated')):
            with self.assertRaises(IntegrityError): create_category(actor=self.admin,name='AUD03 new')
        self.assertEqual(Category.objects.count(),0)

    def test_error_description_points_to_visible_error(self):
        response=self.client.post(reverse('category-create'),{'name':''})
        self.assertContains(response,'aria-describedby="id_name_error"')
        self.assertContains(response,'id="id_name_error"')
        self.assertContains(response,'role="alert"')


class CategoryMigrationAudit03Tests(TestCase):
    def test_legacy_key_normalizes_without_renaming_or_relinking(self):
        from catalog.models import Product
        category=Category.objects.create(name='AUD03 Legacy')
        Category.objects.filter(pk=category.pk).update(name=' AUD03   Legacy ',name_normalized=' aud03   legacy ')
        product=Product.objects.create(category=category,name='AUD03',barcode='AUD03',sale_price=Decimal('1.00'))
        module=import_module('catalog.migrations.0003_normalize_category_spaces')
        module.normalize_category_keys(apps,SimpleNamespace(connection=SimpleNamespace(alias='default')))
        category.refresh_from_db();product.refresh_from_db()
        self.assertEqual(category.name,' AUD03   Legacy ')
        self.assertEqual(category.name_normalized,'aud03 legacy')
        self.assertEqual(product.category_id,category.pk)

    def test_collision_aborts_before_any_key_changes(self):
        first=Category.objects.create(name='AUD03 First')
        second=Category.objects.create(name='AUD03 Second')
        Category.objects.filter(pk=first.pk).update(name='AUD03   Collision',name_normalized='aud03   collision')
        Category.objects.filter(pk=second.pk).update(name='AUD03 Collision',name_normalized='aud03 collision')
        before=list(Category.objects.order_by('pk').values())
        module=import_module('catalog.migrations.0003_normalize_category_spaces')
        with self.assertRaisesMessage(RuntimeError,'normalization collision'):
            module.normalize_category_keys(apps,SimpleNamespace(connection=SimpleNamespace(alias='default')))
        self.assertEqual(list(Category.objects.order_by('pk').values()),before)


class CategoryEffectsAudit03Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        CategoryAudit03Tests.setUpTestData.__func__(cls)

    def test_category_blocks_direct_services_preserving_draft_stock_and_history(self):
        from catalog.models import Product
        from inventory.models import Lot,InitialInventoryLoad
        from inventory.services import confirm_initial_load,register_stock_entry,LotInput
        from sales.models import Sale,SaleLine,SaleDraft,SaleDraftLine
        from sales.services import add_product_to_draft,update_draft_line,checkout_sale
        from cash.models import CashRegister,CashShift
        from cash.services import open_cash_shift
        category=Category.objects.create(name='AUD03 integration')
        product=Product.objects.create(category=category,name='AUD03 Loaded',barcode='AUD03-LOADED',sale_price=Decimal('8.50'))
        empty=Product.objects.create(category=category,name='AUD03 Empty',barcode='AUD03-EMPTY',sale_price=Decimal('4.00'))
        lots=[LotInput('AUD03-LOT',20,Decimal('5.00'),timezone.localdate()+timedelta(days=30))]
        warehouse=self.actors['ALMACENERO'];seller=self.actors['VENDEDOR']
        confirm_initial_load(actor=warehouse,product=product,lots=lots)
        CashRegister.objects.create(code='CAJA-01')
        open_cash_shift(actor=seller,opening_amount=Decimal('50.00'))
        old=add_product_to_draft(actor=seller,product_id=product.pk,quantity=1)
        sale=checkout_sale(actor=seller,draft_id=old.pk,cash_received=Decimal('10.00'),idempotency_key=uuid.uuid4())
        draft=add_product_to_draft(actor=seller,product_id=product.pk,quantity=2)
        line=draft.lines.get()
        def snapshot():
            return {m._meta.label:list(m.objects.order_by('pk').values()) for m in [Product,Lot,InitialInventoryLoad,Sale,SaleLine,SaleDraft,SaleDraftLine,CashShift]}
        before=snapshot()
        toggle_category_status(actor=self.admin,category=category)
        for operation in [
            lambda: confirm_initial_load(actor=warehouse,product=empty,lots=lots),
            lambda: register_stock_entry(actor=warehouse,product=product,lots=[LotInput('AUD03-NEW',3,Decimal('5.00'),timezone.localdate()+timedelta(days=31))]),
            lambda: add_product_to_draft(actor=seller,product_id=product.pk,quantity=1),
            lambda: update_draft_line(actor=seller,line_id=line.pk,quantity=3),
            lambda: checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('20.00'),idempotency_key=uuid.uuid4()),
        ]:
            with self.assertRaises(ValidationError): operation()
            self.assertEqual(snapshot(),before)
        toggle_category_status(actor=self.admin,category=category)
        self.assertEqual(snapshot(),before)
        product.refresh_from_db()
        self.assertTrue(product.is_sellable)
        self.assertEqual(product.physical_stock,19)
        self.assertEqual(sale.lines.get().product_snapshot_name,'AUD03 Loaded')
