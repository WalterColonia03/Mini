# Informe de verificación en servidor · Sublote 02-E (14/11/2026)

- **Inicio UTC:** `2026-11-15T02:44:24.357274+00:00`
- **Fin UTC:** `2026-11-15T02:48:49.550164+00:00`
- **Base protegida (`r1_pmv.sqlite3`) intacta:** `True` (`sha256`: `c60b4027d4d2f0953ddcbb828cd6412e9889f9794537de9c50aed7f92fdded58`)

## Comandos ejecutados

1. `python manage.py check` -> código `0` (`OK`)
2. `python manage.py makemigrations --check --dry-run` -> código `0` (`OK`)
3. `python manage.py test identity app_platform catalog inventory cash sales tests -v 2` -> código `0` (`OK`)

## Cierre de suite completa

```text
test_nullable_migration_preserves_old_rows_and_lot_instant_guard (inventory.test_audit14h_initial_history.InitialHistoryMigrationTests.test_nullable_migration_preserves_old_rows_and_lot_instant_guard) ... ok
test_stage12_migrations_round_trip_and_no_pending_migrations (sales.test_audit12_receipts_history.Stage12MigrationOrderingTests.test_stage12_migrations_round_trip_and_no_pending_migrations) ... ok
test_upgrade_preserves_unknown_history_without_fefo_backfill (sales.test_audit14f_allocations.LegacyAllocationMigrationTests.test_upgrade_preserves_unknown_history_without_fefo_backfill) ... ok

----------------------------------------------------------------------
Ran 652 tests in 252.300s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...

```
