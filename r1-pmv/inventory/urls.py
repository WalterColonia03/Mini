from django.urls import path

from . import views

urlpatterns = [
    # Carga inicial (Sprint 1) y entradas posteriores (HU-INV-01b)
    path("carga-inicial/", views.initial_load_create, name="inventory-load"),
    path("carga-inicial/<uuid:load_id>/creada/", views.initial_load_created, name="inventory-load-created-alias"),
    path("cargas/<uuid:load_id>/", views.initial_load_created, name="inventory-load-created"),
    path("entrada/", views.stock_entry_create, name="stock-entry"),
    path("recepciones/<uuid:receipt_id>/", views.stock_receipt_detail, name="stock-receipt"),
    # HU-PROV-01, HU-PROV-02, HU-PROV-04 — Proveedores
    path("proveedores/", views.supplier_list, name="supplier-list"),
    path("proveedores/nuevo/", views.supplier_create, name="supplier-create"),
    path("proveedores/<uuid:supplier_id>/estado/", views.supplier_toggle, name="supplier-toggle"),
    # HU-INV-02 — Baja por merma
    path("bajas/nueva/", views.stock_writeoff_create, name="stock-writeoff"),
    path("bajas/<uuid:writeoff_id>/", views.stock_writeoff_receipt, name="stock-writeoff-receipt"),
    # HU-INV-03 — Ajuste fisico
    path("ajustes/nuevo/", views.physical_adjustment_create, name="physical-adjustment"),
    path("ajustes/<uuid:adjustment_id>/", views.physical_adjustment_detail, name="physical-adjustment-detail"),
    # HUECO-01 + HUECO-02 — HU-INV-04 — Stock overview con alertas
    path("stock/", views.stock_overview, name="stock-overview"),
    # HUECO-03 — HU-INV-06 — Historial de movimientos por producto
    path("productos/<uuid:product_id>/movimientos/", views.product_movements, name="product-movements"),
]
