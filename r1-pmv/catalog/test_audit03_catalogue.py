"""PROD01 catalogue: visible stock, thresholds, literal search and permissions."""
from datetime import datetime,timedelta,timezone as tz
from decimal import Decimal
from html.parser import HTMLParser
from unittest.mock import patch

from django.test import Client,TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Category,Product
from identity.models import Account,Role
from inventory.models import InitialInventoryLoad,Lot

class CatalogueTable(HTMLParser):
    def __init__(self,html):
        super().__init__();self.rows=[];self.headers=[];self.row=None;self.cell=None;self.tag=None;self.feed(html)
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        elif tag in ('td','th') and self.row is not None:self.cell=[];self.tag=tag
    def handle_data(self,text):
        if self.cell is not None:self.cell.append(text)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            text=' '.join(''.join(self.cell).split());self.row.append(text);self.cell=None
            if tag=='th':self.headers.append(text)
        if tag=='tr' and self.row is not None:
            if self.row and self.tag=='td':self.rows.append(dict(zip(self.headers,self.row)))
            self.row=None

class CatalogueAudit03Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actors={}
        for code in ['ADMIN','ALMACENERO','VENDEDOR']:
            role=Role.objects.create(code=code,name=code)
            cls.actors[code]=Account.objects.create_user(code.lower()+'@audit03b.invalid',None,display_name='AUD03B '+code,role=role)
        cls.category=Category.objects.create(name='AUD03B Conservas')
    def setUp(self):self.client.force_login(self.actors['ADMIN'])
    def product(self,code='CODE',name='AUD03B Producto',minimum=10,active=True,category=None,lots=()):
        p=Product.objects.create(category=category or self.category,name=name,barcode=code,sale_price=Decimal('8.50'),minimum_stock=minimum,is_active=active)
        if lots:
            load=InitialInventoryLoad.objects.create(product=p,responsible=self.actors['ALMACENERO'])
            for i,(qty,date) in enumerate(lots):
                Lot.objects.create(product=p,initial_load=load,number=f'L{i}',initial_quantity=max(qty,1),available_quantity=qty,unit_cost=Decimal('1.00'),expiration_date=date)
        return p
    def table(self,client=None,q=None):
        response=(client or self.client).get(reverse('product-list'),{} if q is None else {'q':q})
        self.assertEqual(response.status_code,200)
        return CatalogueTable(response.content.decode()),response
    def test_catalogue_reports_all_commercial_columns_and_current_stock(self):
        tomorrow=timezone.localdate()+timedelta(days=1)
        self.product(lots=[(5,tomorrow),(5,tomorrow)])
        table,_=self.table();row=table.rows[0]
        self.assertEqual(row['Nombre'],'AUD03B Producto');self.assertEqual(row['Código de barras'],'CODE')
        self.assertEqual(row['Categoría'],'AUD03B Conservas');self.assertEqual(row['Precio (S/)'],'8,50')
        self.assertEqual(row.get('Existencias vigentes (UND)'),'10 Stock bajo')
    def test_alert_uses_configured_inclusive_threshold_and_zero(self):
        tomorrow=timezone.localdate()+timedelta(days=1)
        for stock,minimum in [(0,10),(9,10),(10,10),(11,10),(0,0),(4,3),(3,3)]:
            self.product(code=f'S{stock}M{minimum}',name=f'Caso{stock}-{minimum}',minimum=minimum,lots=[(stock,tomorrow)] if stock else [])
        table,_=self.table()
        for row in table.rows:
            code=row['Código de barras'];stock,minimum=map(int,code[1:].split('M'))
            expected=f'{stock}'+(' Stock bajo' if stock<=minimum else '')
            with self.subTest(code=code):self.assertEqual(row.get('Existencias vigentes (UND)'),expected)
    def test_expired_today_and_exhausted_lots_do_not_inflate_stock(self):
        today=timezone.localdate()
        self.product(lots=[(4,today+timedelta(days=1)),(5,today+timedelta(days=2)),(50,today-timedelta(days=1)),(3,today),(0,today+timedelta(days=3))])
        table,_=self.table();self.assertEqual(table.rows[0].get('Existencias vigentes (UND)'),'9 Stock bajo')
    def test_expiration_cutoff_uses_lima_not_utc_date(self):
        now=datetime(2026,11,10,4,30,tzinfo=tz.utc)
        with patch('django.utils.timezone.now',return_value=now):
            self.product(lots=[(2,datetime(2026,11,9).date()),(7,datetime(2026,11,10).date())])
            table,_=self.table();self.assertEqual(table.rows[0].get('Existencias vigentes (UND)'),'7 Stock bajo')
    def test_inactive_states_preserve_stock_and_are_not_available(self):
        tomorrow=timezone.localdate()+timedelta(days=1)
        self.product(code='OFF',active=False,lots=[(8,tomorrow)])
        other=Category.objects.create(name='Suspendida',is_active=False)
        self.product(code='CATOFF',name='AUD03B categoría inactiva',category=other,lots=[(9,tomorrow)])
        table,_=self.table();rows={r['Código de barras']:r for r in table.rows}
        self.assertEqual(rows['OFF']['Disponibilidad'],'Inactivo')
        self.assertEqual(rows['CATOFF']['Disponibilidad'],'Categoría desactivada')
        self.assertEqual(rows['OFF'].get('Existencias vigentes (UND)'),'8')
        self.assertEqual(rows['CATOFF'].get('Existencias vigentes (UND)'),'9')
    def test_search_name_code_case_partial_and_barcode_normalization(self):
        self.product(code='AB- 001',name='Atún AUD03B clásico')
        self.product(code='XY-002',name='Otro producto')
        for query in ['AUD03B','aud03b','Atún','ATÚN','ATU\u0301N',' AB-001 ','a b- 0 0 1','００１']:
            with self.subTest(query=query):
                table,_=self.table(q=query);self.assertEqual([r['Código de barras'] for r in table.rows],['AB- 001'])
        self.assertFalse(self.table(q='Atun')[0].rows)

    def test_name_search_follows_partial_save_without_modifying_display_name(self):
        product = self.product(name='Atún claro')
        product.name = 'Piña'
        product.save(update_fields=['name'])
        self.assertFalse(self.table(q='ATÚN')[0].rows)
        rows = self.table(q='PIÑA')[0].rows
        self.assertEqual([row['Nombre'] for row in rows], ['Piña'])
    def test_search_empty_spaces_missing_and_literal_wildcards(self):
        self.product();self.product(code='SECOND',name='Otro')
        for query in [None,'','   ']:self.assertEqual(len(self.table(q=query)[0].rows),2)
        for query in ['%','_',"' OR 1=1 --",'<script>alert(1)</script>','X'*4096,'\x00']:
            with self.subTest(query=query):
                table,response=self.table(q=query);self.assertEqual(table.rows,[])
                self.assertNotContains(response,'<script>alert(1)</script>')
                if '\x00' in query:
                    self.assertContains(response,'La búsqueda contiene un carácter no válido.')
                    self.assertNotIn(b'\x00',response.content)
    def test_empty_and_no_match_messages_and_clear_link(self):
        _,empty=self.table();self.assertContains(empty,'No hay productos registrados.')
        self.product();_,missing=self.table(q='ninguno')
        self.assertContains(missing,'No se encontraron productos con «ninguno».')
        self.assertContains(missing,'aria-label="Limpiar búsqueda"')
    def test_warehouse_has_same_data_without_actions_and_seller_denied(self):
        self.product()
        warehouse=Client();warehouse.force_login(self.actors['ALMACENERO'])
        admin,_=self.table();table,response=self.table(client=warehouse)
        self.assertNotIn('Acciones',table.headers)
        self.assertEqual({k:v for k,v in admin.rows[0].items() if k!='Acciones'},table.rows[0])
        self.assertNotContains(response,'>Editar<');self.assertNotContains(response,'>Deshabilitar<')
        seller=Client();seller.force_login(self.actors['VENDEDOR'])
        self.assertEqual(seller.get(reverse('product-list')).status_code,403)
        self.assertEqual(Client().get(reverse('product-list')).status_code,302)
    def test_requests_do_not_write_and_non_get_methods_are_denied(self):
        self.product()
        before=list(Product.objects.values());lots=list(Lot.objects.values())
        for method in ['post','put','patch','delete']:
            response=getattr(self.client,method)(reverse('product-list'),{'name':'injected','minimum_stock':0})
            self.assertEqual(response.status_code,405)
        for query in ['CODE','missing','%']:
            self.table(q=query)
        self.assertEqual(list(Product.objects.values()),before);self.assertEqual(list(Lot.objects.values()),lots)
