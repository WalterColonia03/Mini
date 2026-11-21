# Evidencia — S2-PROD01-AUTO · HU-PROD-01

**HU:** HU-PROD-01 · Ver catálogo completo de productos  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede ver el catálogo (HTTP 200) | `ProductListTests.test_admin_sees_product_list` | ✅ ok |
| CA-2: ALMACENERO puede ver el catálogo (HTTP 200) | `ProductListTests.test_warehouse_sees_product_list` | ✅ ok |
| CA-3: Rol VENDEDOR recibe 403 | `ProductListTests.test_seller_gets_403` | ✅ ok |
| CA-4: Búsqueda por nombre filtra resultados correctamente | `ProductListTests.test_search_filters_by_name` | ✅ ok |

## Comando y resultado real

```
python manage.py test --verbosity=1
APP_ENV=test  DJANGO_SECRET_KEY=local-test-key
Base de datos: SQLite en memoria (aislada)

Ran 126 tests in 7.664s
OK
System check identified no issues (0 silenced).
```

## Resultado

**Completada ✅** — Vista `product_list` con filtro de búsqueda `?q=`. Template `catalog/product_list.html` con badges de disponibilidad. URL `/productos/`.

