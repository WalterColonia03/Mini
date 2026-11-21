from django.urls import include, path

urlpatterns = [
    # The commercial application has no Django-admin endpoint. Maintenance
    # requires a separately secured channel instead of another login path.
    path("productos/", include("catalog.urls")),
    path("inventario/", include("inventory.urls")),
    path("caja/", include("cash.urls")),
    path("ventas/", include("sales.urls")),
    path("", include("identity.urls")),
]
