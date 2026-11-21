# Evidencia — S2-PROD05-AUTO · HU-PROD-05

**HU:** HU-PROD-05 · Gestionar estado de disponibilidad  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede cambiar disponibilidad (toggle is_active) | `ProductToggleTests.test_admin_toggles_availability` | ✅ ok |
| CA-2: Rol no-ADMIN recibe 403 | `ProductToggleTests.test_non_admin_gets_403` | ✅ ok |

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

**Completada ✅** — Service `toggle_product_availability()` y vista `product_toggle_availability` (POST). URL `/productos/<uuid>/disponibilidad/`.

