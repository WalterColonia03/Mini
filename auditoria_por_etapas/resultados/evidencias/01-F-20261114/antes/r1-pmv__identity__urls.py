from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("inicio/", views.dashboard, name="dashboard"),
    path("salir/", views.logout_view, name="logout"),
    path("empleados/", views.employee_list, name="employee-list"),
    path("empleados/nuevo/", views.employee_create, name="employee-create"),
    path("empleados/<uuid:account_id>/editar/", views.employee_edit, name="employee-edit"),
    path("empleados/<uuid:account_id>/estado/", views.employee_deactivate, name="employee-deactivate"),
]
