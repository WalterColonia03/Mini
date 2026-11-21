from django.urls import path

from . import views

urlpatterns = [
    path("", views.sales_draft, name="sales-draft"),
    path("cobrar/", views.sales_checkout, name="sales-checkout"),
    path("constancia/<uuid:sale_id>/", views.sales_receipt, name="sales-receipt"),
    path("lineas/<uuid:line_id>/", views.sales_line_update, name="sales-line-update"),
    path("lineas/<uuid:line_id>/quitar/", views.sales_line_remove, name="sales-line-remove"),
    path("descartar/", views.sales_draft_discard, name="sales-draft-discard"),
    path("historial/turno/", views.sales_shift_history, name="sales-shift-history"),
    path("historial/", views.sales_history, name="sales-history"),
]
