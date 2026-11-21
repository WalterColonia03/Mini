# Evidencia — S2-PROD04-AUTO · HU-PROD-04

**HU:** HU-PROD-04 · Editar datos de un producto  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede editar nombre del producto y es redirigido | `ProductEditTests.test_admin_can_edit_product_name` | ✅ ok |
| CA-2: Código de barras duplicado es rechazado | `ProductEditTests.test_duplicate_barcode_is_rejected` | ✅ ok |
| CA-3: Rol no-ADMIN recibe 403 | `ProductEditTests.test_non_admin_gets_403` | ✅ ok |

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

**Completada ✅** — Service `update_product()` y `ProductEditForm` (ModelForm con exclusión de validación de categoría). Vista `product_edit`. Template `catalog/product_edit.html`. URL `/productos/<uuid>/editar/`.

