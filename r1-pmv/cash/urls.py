from django.urls import path

from . import views

urlpatterns = [
    path("abrir/", views.cash_open, name="cash-open"),
    path("cerrar/", views.cash_close, name="cash-close"),
    path("turnos/<uuid:shift_id>/abierto/", views.cash_shift_opened, name="cash-shift-opened"),
    path("turnos/<uuid:shift_id>/cerrado/", views.cash_shift_closed, name="cash-shift-closed"),
    path("turnos/", views.cash_shift_history, name="cash-shift-history"),
]
