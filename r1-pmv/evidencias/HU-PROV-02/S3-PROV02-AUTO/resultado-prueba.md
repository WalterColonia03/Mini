# Evidencia — S3-PROV02-AUTO · HU-PROV-02

**HU:** HU-PROV-02 · Registrar nuevo proveedor  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin puede registrar un nuevo proveedor con nombre, RUC y teléfono | `SupplierTests.test_admin_creates_supplier` | ✅ ok |
| CA-2: RUC duplicado es rechazado | `SupplierTests.test_duplicate_ruc_is_rejected` | ✅ ok |

## Implementación técnica

- **Servicio:** `inventory/services.py` → `create_supplier(actor, name, ruc, phone)`
- **Formulario:** `inventory/forms.py` → `SupplierForm`
- **Vista:** `inventory/views.py` → `supplier_create(request)`
- **URL:** `/inventario/proveedores/nuevo/` → `supplier-create`
- **Plantilla:** `inventory/templates/inventory/supplier_form.html`

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

**Completada ✅** — El administrador puede registrar nuevos proveedores mediante el formulario en `/inventario/proveedores/nuevo/`. El servicio `create_supplier()` valida que el nombre y RUC no estén vacíos y que el RUC no esté ya registrado. Tras el registro exitoso redirige a la lista de proveedores.

