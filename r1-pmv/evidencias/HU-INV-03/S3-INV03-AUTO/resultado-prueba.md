# Evidencia — S3-INV03-AUTO · HU-INV-03

**HU:** HU-INV-03 · Ajuste por conteo físico  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin puede registrar un ajuste positivo (sobrante detectado en conteo) | `PhysicalAdjustmentTests.test_admin_registers_positive_adjustment` | ✅ ok |
| CA-2: Ajuste negativo que supera existencias es rechazado | `PhysicalAdjustmentTests.test_negative_adjustment_exceeding_stock_is_rejected` | ✅ ok |
| CA-3: Delta de cero es rechazado por el formulario | `PhysicalAdjustmentTests.test_zero_delta_is_rejected_by_form` | ✅ ok |
| CA-4: Almacenero obtiene 403 (solo admin puede ajustar) | `PhysicalAdjustmentTests.test_warehouse_gets_403` | ✅ ok |

## Implementación técnica

- **Modelo:** `inventory/models.py` → `PhysicalAdjustment(lot, delta, reason, responsible, created_at)`
- **Servicio:** `inventory/services.py` → `register_physical_adjustment(actor, lot, delta, reason)`
- **Lógica de ajuste positivo:** cuando `delta > 0`, se actualiza también `initial_quantity` para mantener el invariante `available_quantity <= initial_quantity` (constraint `lot_available_lte_initial`)
- **Formulario:** `inventory/forms.py` → `PhysicalAdjustmentForm`
- **Vista:** `inventory/views.py` → `physical_adjustment_create(request)`
- **URL:** `/inventario/ajuste/` → `physical-adjustment`
- **Plantilla:** `inventory/templates/inventory/adjustment_form.html`

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

**Completada ✅** — El administrador puede registrar ajustes de inventario positivos (sobrantes) o negativos (faltantes) por conteo físico. La operación es atómica: crea el registro `PhysicalAdjustment` y actualiza `Lot.available_quantity` (y `initial_quantity` si el ajuste es positivo) en la misma transacción. El almacenero no tiene acceso a esta función.

