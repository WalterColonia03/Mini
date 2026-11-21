# Evidencia — S2-CAT02-AUTO · HU-CAT-02

**HU:** HU-CAT-02 · Crear nueva categoría  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede crear categoría válida y es redirigido | `CategoryCreateTests.test_admin_creates_category` | ✅ ok |
| CA-2: Nombre duplicado (case-insensitive) es rechazado | `CategoryCreateTests.test_duplicate_name_is_rejected` | ✅ ok |
| CA-3: Rol no-ADMIN recibe 403 en POST | `CategoryCreateTests.test_non_admin_post_is_forbidden` | ✅ ok |

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

**Completada ✅** — Service `create_category()` y vista `category_create` implementados. Template `catalog/category_form.html`. URL `/productos/categorias/nueva/`.

