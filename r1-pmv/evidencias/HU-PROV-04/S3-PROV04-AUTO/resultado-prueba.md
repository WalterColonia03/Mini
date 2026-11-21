# Evidencia — S3-PROV04-AUTO · HU-PROV-04

**HU:** HU-PROV-04 · Gestionar estado de vigencia del proveedor  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin puede alternar el estado activo/inactivo de un proveedor | `SupplierTests.test_admin_toggles_supplier_status` | ✅ ok |

## Implementación técnica

- **Servicio:** `inventory/services.py` → `toggle_supplier_status(actor, supplier)`
- **Vista:** `inventory/views.py` → `supplier_toggle(request, supplier_id)` (POST only)
- **URL:** `/inventario/proveedores/<uuid>/estado/` → `supplier-toggle`
- **Plantilla:** botón de acción en `inventory/templates/inventory/supplier_list.html`

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

**Completada ✅** — El administrador puede activar o desactivar proveedores mediante POST a `/inventario/proveedores/<uuid>/estado/`. La operación implementa un toggle automático sobre el campo `is_active`. Solo el rol ADMIN puede ejecutar esta acción. La lista de proveedores muestra el estado vigente de cada uno.

