# Evidencia — S3-INV02-AUTO · HU-INV-02

**HU:** HU-INV-02 · Registrar baja de inventario por merma  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin o almacenero pueden registrar una baja de inventario con correlativo | `StockWriteOffTests.test_admin_registers_writeoff` | ✅ ok |
| CA-2: Almacenero puede acceder a la página de baja | `StockWriteOffTests.test_warehouse_accesses_writeoff_page` | ✅ ok |
| CA-3: Cantidad superior a existencias es rechazada | `StockWriteOffTests.test_quantity_exceeding_stock_is_rejected` | ✅ ok |
| CA-4: Motivo «Daño o rotura» requiere notas obligatorias | `StockWriteOffTests.test_damage_reason_requires_notes` | ✅ ok |

## Implementación técnica

- **Modelo:** `inventory/models.py` → `StockWriteOff(lot, quantity, reason, notes, responsible, correlativo, created_at)`
- **Servicio:** `inventory/services.py` → `write_off_stock(actor, lot, quantity, reason, notes)`
- **Correlativo:** formato `B-{count:08d}` (ej. `B-00000001`)
- **Formulario:** `inventory/forms.py` → `StockWriteOffForm`
- **Vista:** `inventory/views.py` → `stock_writeoff_create(request)`
- **URL:** `/inventario/bajas/nueva/` → `stock-writeoff`
- **Plantilla:** `inventory/templates/inventory/writeoff_form.html`

## Lógica de negocio validada

- Lote vencido → motivo forzado a «Vencimiento»
- Motivo «Daño» o «Robo» → notas obligatorias
- Cantidad a dar de baja descuenta `available_quantity` del lote en la misma transacción

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

**Completada ✅** — El sistema permite registrar bajas de inventario por merma con correlativo autogenerado (`B-XXXXXXXX`). La operación es atómica: crea el registro `StockWriteOff` y decrementa `Lot.available_quantity` en la misma transacción. Se validan el motivo (vencimiento, daño, robo) y la obligatoriedad de notas para ciertos motivos.

