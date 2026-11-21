# Evidencia — S1-VEN01C-AUTO · SCRUM-343

**HU:** HU-VEN-01c · Cobrar en efectivo y descontar existencias  
**Inicio real:** 2026-11-04T22:01:00-05:00  
**Fin real:** 2026-11-04T22:01:44-05:00  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Pago exacto completa venta, descuenta lotes FEFO y registra snapshots | `test_exact_payment_creates_sale_and_deducts_lot_stock` | ✅ ok |
| CA-2: Pago insuficiente no crea venta ni modifica lotes | `test_insufficient_cash_rejected_no_sale_no_stock_change` | ✅ ok |
| CA-3: Efectivo mayor al total calcula vuelto correcto | `test_overpayment_records_correct_change` | ✅ ok |
| CA-4: Reintento con la misma clave de idempotencia devuelve la misma venta | `test_duplicate_idempotency_key_returns_same_sale` | ✅ ok |
| CA-5: Dos ventas distintas tienen correlativos únicos secuenciales | `test_two_different_sales_get_unique_sequential_correlatives` | ✅ ok |
| CA-6: Rol no-SELLER recibe 403 | `test_non_seller_roles_cannot_access_checkout` | ✅ ok |

## Comando y resultado real

```
python manage.py test sales --verbosity=1
APP_ENV=test  DJANGO_SECRET_KEY=local-test-key
Base de datos: SQLite en memoria (aislada)

Ran 95 tests in 5.635s
OK
System check identified no issues (0 silenced).
```

## Resultado

**Completada ✅** — Los 6 criterios de aceptación de HU-VEN-01c cubiertos con pruebas automatizadas verdes. Servicio `checkout_sale` implementado con FEFO atómico, correlativo global e idempotencia dentro de `transaction.atomic()`. Suite ejecutada sobre base SQLite aislada, sin secretos en evidencia.

