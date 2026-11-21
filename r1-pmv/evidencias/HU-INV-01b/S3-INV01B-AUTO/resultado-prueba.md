# Evidencia — S3-INV01B-AUTO · HU-INV-01b

**HU:** HU-INV-01b · Recalcular costo promedio en entradas posteriores  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Entrada posterior de lotes se registra correctamente cuando ya existe carga inicial | `PhysicalAdjustmentTests.test_stock_entry_view_registers_subsequent_lots_and_links_supplier` | ✅ ok |
| CA-2: El costo promedio ponderado se recalcula sobre todos los lotes con existencias > 0 | `PhysicalAdjustmentTests.test_stock_entry_view_registers_subsequent_lots_and_links_supplier` | ✅ ok |
| CA-3: Se rechaza entrada posterior si el producto no tiene carga inicial | Validado en servicio `register_stock_entry` y `StockEntryProductForm` | ✅ ok |
| CA-4: Solo el almacenero puede registrar entradas posteriores | Validado por `@roles_required(Role.Code.WAREHOUSE)` y `PermissionDenied` en `register_stock_entry` | ✅ ok |

## Implementación técnica

- **Servicio:** `inventory/services.py` → `register_stock_entry(actor, product, lots, supplier=None, business_date=None)`
- **Vista y Formulario:** `inventory/views.py` → `stock_entry_create`, `inventory/forms.py` → `StockEntryProductForm`, plantilla `inventory/templates/inventory/stock_entry_form.html`
- **Lógica de recálculo:** promedio ponderado `Σ(unit_cost × available_quantity) / Σ(available_quantity)` sobre todos los lotes activos
- **Reutiliza:** `InitialInventoryLoad` existente como FK para los nuevos lotes y permite asociar `Supplier` (`Lot.supplier`)
- **URL:** `/inventario/entrada/` → `stock-entry`

## Comando y resultado real

```
python manage.py test --verbosity=1
APP_ENV=test  DJANGO_SECRET_KEY=local-test-key-prompt
Base de datos: SQLite en memoria (aislada)

Ran 183 tests in 12.809s
OK
System check identified no issues (0 silenced).
```

## Resultado

**Completada ✅** — El servicio `register_stock_entry()` permite registrar lotes adicionales para un producto que ya tiene carga inicial confirmada. Tras cada entrada, recalcula el costo promedio ponderado considerando todos los lotes con existencias disponibles y actualiza `Product.average_cost`. Solo el almacenero tiene permiso para esta operación.

