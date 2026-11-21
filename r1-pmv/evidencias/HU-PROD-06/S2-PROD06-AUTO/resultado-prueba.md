# Evidencia — S2-PROD06-AUTO · HU-PROD-06

**HU:** HU-PROD-06 · Consultar vencimientos de productos  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede acceder a la vista de vencimientos | `ProductExpirationsTests.test_admin_accesses_expirations_page` | ✅ ok |
| CA-2: ALMACENERO puede acceder a la vista de vencimientos | `ProductExpirationsTests.test_warehouse_accesses_expirations_page` | ✅ ok |
| CA-3: Rol VENDEDOR recibe 403 | `ProductExpirationsTests.test_seller_gets_403` | ✅ ok |

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

**Completada ✅** — Vista `product_expirations` con filtro `?dias=` (default 30). Consulta lotes de `inventory.Lot` con `available_quantity>0` y `expiration_date<=cutoff`. Template `catalog/product_expirations.html`. URL `/productos/vencimientos/`.

