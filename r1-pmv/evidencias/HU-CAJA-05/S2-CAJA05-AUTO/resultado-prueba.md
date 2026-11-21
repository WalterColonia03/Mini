# Evidencia — S2-CAJA05-AUTO · HU-CAJA-05

**HU:** HU-CAJA-05 · Historial de turnos de caja  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: VENDEDOR puede ver el historial de turnos | `CashShiftHistoryTests.test_seller_can_see_shift_history` | ✅ ok |
| CA-2: ADMIN puede ver el historial de turnos | `CashShiftHistoryTests.test_admin_can_see_shift_history` | ✅ ok |
| CA-3: ALMACENERO recibe 403 | `CashShiftHistoryTests.test_warehouse_gets_403` | ✅ ok |

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

**Completada ✅** — Vista `cash_shift_history` con `@roles_required(ADMIN, SELLER)`. Lista todos los turnos con apertura y cierre. Template `cash/cash_shift_history.html`. URL `/caja/turnos/`.

