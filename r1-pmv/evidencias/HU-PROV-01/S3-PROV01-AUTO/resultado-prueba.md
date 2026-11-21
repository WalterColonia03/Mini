# Evidencia — S3-PROV01-AUTO · HU-PROV-01

**HU:** HU-PROV-01 · Ver lista de proveedores  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin puede ver la lista de proveedores | `SupplierTests.test_admin_sees_supplier_list` | ✅ ok |
| CA-2: Almacenero también puede ver la lista (solo lectura) | `SupplierTests.test_warehouse_sees_supplier_list` | ✅ ok |
| CA-3: Búsqueda filtra proveedores por nombre | `SupplierTests.test_search_filters_by_name` | ✅ ok |

## Implementación técnica

- **Modelo:** `inventory/models.py` → `Supplier(name, ruc, phone, is_active, created_at, updated_at)`
- **Vista:** `inventory/views.py` → `supplier_list(request)` con filtro por `q` y `estado`
- **URL:** `/inventario/proveedores/` → `supplier-list`
- **Plantilla:** `inventory/templates/inventory/supplier_list.html`

## Comando y resultado real

```
python manage.py test --verbosity=1
APP_ENV=test  DJANGO_SECRET_KEY=local-test-key
Base de datos: SQLite en memoria (aislada)

Ran 152 tests in 9.667s
OK
System check identified no issues (0 silenced).
```

## Resultado

**Completada ✅** — La vista `/inventario/proveedores/` muestra todos los proveedores registrados con su nombre, RUC, teléfono y estado (activo/inactivo). Soporta filtrado por nombre mediante parámetro `q`. Accesible por administrador y almacenero.

