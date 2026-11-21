# Evidencia — S1-CAJA02-AUTO · SCRUM-353

**HU:** HU-CAJA-02 · Cerrar y cuadrar la caja  
**Inicio real:** 2026-11-04T22:01:00-05:00  
**Fin real:** 2026-11-04T22:01:44-05:00  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Cierre con exacto → diferencia = 0 | `test_close_exact_amount_records_zero_difference` | ✅ ok |
| CA-2: Cierre con sobrante → diferencia > 0 | `test_close_surplus_records_positive_difference` | ✅ ok |
| CA-3: Cierre con faltante → diferencia < 0 | `test_close_shortage_records_negative_difference` | ✅ ok |
| CA-4: Borrador activo con líneas bloquea el cierre | `test_close_blocked_when_active_draft_has_lines` | ✅ ok |
| CA-5: Doble cierre no duplica el acta | `test_double_close_does_not_create_duplicate` | ✅ ok |
| Extra: Rol no-SELLER recibe 403 | `test_non_seller_roles_cannot_close_shift` | ✅ ok |
| Extra: Acta de cierre muestra importes correctos | `test_closed_shift_detail_shows_correct_amounts` | ✅ ok |

## Comando y resultado real

```
python manage.py test sales cash --verbosity=1
APP_ENV=test  DJANGO_SECRET_KEY=local-test-key
Base de datos: SQLite en memoria (aislada)

Ran 95 tests in 5.635s
OK
System check identified no issues (0 silenced).
```

## Resultado

**Completada ✅** — Los 5 criterios de aceptación de HU-CAJA-02 cubiertos con pruebas automatizadas verdes. El servicio `close_cash_shift` calcula `expected = opening_amount + SUM(sale.total_amount)`, bloquea el turno con `select_for_update`, rechaza cierres con borradores activos con líneas y hace el cierre atómico. Suite ejecutada sobre base SQLite aislada, sin secretos en evidencia.

