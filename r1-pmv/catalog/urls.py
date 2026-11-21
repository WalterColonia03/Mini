from django.urls import path

from . import views

urlpatterns = [
    # Categorías
    path("categorias/", views.category_list, name="category-list"),
    path("categorias/nueva/", views.category_create, name="category-create"),
    path("categorias/<uuid:category_id>/estado/", views.category_toggle, name="category-toggle"),
    path("categorias/<uuid:category_id>/estado/confirmar/", views.category_state_confirm, name="category-state-confirm"),
    # Vencimientos
    path("vencimientos/", views.product_expirations, name="product-expirations"),
    # Productos
    path("", views.product_list, name="product-list"),
    path("nuevo/", views.product_create, name="product-entry"),
    path("codigos/comprobar/", views.product_barcode_check, name="product-barcode-check"),
    path("<uuid:product_id>/registrado/", views.product_created, name="product-created"),
    path("<uuid:product_id>/creado/", views.product_created, name="product-created-alias"),
    path("<uuid:product_id>/editar/", views.product_edit, name="product-edit"),
    path("<uuid:product_id>/disponibilidad/", views.product_toggle_availability, name="product-toggle"),
]
