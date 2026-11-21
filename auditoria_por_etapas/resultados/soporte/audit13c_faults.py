"""Test-only faults; no public endpoint, only local marker control."""
import json
from django.conf import settings
from django.db import connection, DatabaseError

class QueryFailureMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        marker = settings.RUN_DIR / 'browser-failure.json'
        target = json.loads(marker.read_text()).get('path') if marker.exists() else None
        allowed = {'/inicio/','/inventario/stock/','/productos/vencimientos/','/ventas/historial/'}
        if target not in allowed or request.path != target:
            return self.get_response(request)
        def fail(execute, sql, params, many, context):
            if sql.lstrip().upper().startswith('SELECT') and any(name in sql for name in ['sales_sale','catalog_product','inventory_lot','cash_cashshift']):
                raise DatabaseError('Isolated audit13 query fault')
            return execute(sql, params, many, context)
        with connection.execute_wrapper(fail):
            return self.get_response(request)

