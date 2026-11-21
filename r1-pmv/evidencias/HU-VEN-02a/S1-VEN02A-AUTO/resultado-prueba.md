# Evidencia — S1-VEN02A-AUTO · SCRUM-348

**HU:** HU-VEN-02a · Generar una constancia interna de venta  
**Inicio real:** 2026-11-04T22:01:00-05:00  
**Fin real:** 2026-11-04T22:01:44-05:00  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Muestra correlativo, fecha, vendedor, caja, líneas e importes | `test_receipt_shows_all_required_fields` | ✅ ok |
| CA-2: Los datos son inmutables — snapshots históricos, no recalculados | `test_receipt_uses_snapshots_not_live_product_data` | ✅ ok |
| CA-3: Contiene la leyenda obligatoria (no validez tributaria) | `test_receipt_contains_mandatory_legal_notice` | ✅ ok |
| CA-4: Otro vendedor recibe 404; solo el dueño puede consultar | `test_other_seller_gets_404_for_different_sale` | ✅ ok |

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

**Completada ✅** — Los 4 criterios de aceptación de HU-VEN-02a cubiertos con pruebas automatizadas verdes. La constancia lee snapshots históricos (`product_snapshot_name`, `product_snapshot_barcode`) en lugar de datos en vivo. Template incluye leyenda legal visible y bloque `@media print`. Suite ejecutada sobre base SQLite aislada, sin secretos en evidencia.

