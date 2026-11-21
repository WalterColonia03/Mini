# Evidencia — S2-CAT01-AUTO · HU-CAT-01

**HU:** HU-CAT-01 · Ver lista de categorías  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede ver la lista de categorías (HTTP 200) | `CategoryListTests.test_admin_can_see_category_list` | ✅ ok |
| CA-2: Rol no-ADMIN recibe 403 | `CategoryListTests.test_non_admin_gets_403` | ✅ ok |

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

**Completada ✅** — Vista `category_list` implementada con `@roles_required(ADMIN)`. Template `catalog/category_list.html` creado. URL `/productos/categorias/`.

