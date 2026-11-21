# Informe de verificación en PostgreSQL 18.4 · Sublote 02-E (14/11/2026)

- **Motor:** `PostgreSQL 18.4 on x86_64-windows, compiled by msvc-19.44.35227, 64-bit`
- **Puerto usado y cerrado:** `61077` (`port_closed: True`)
- **Base protegida intacta:** `True` (`c60b4027d4d2f0953ddcbb828cd6412e9889f9794537de9c50aed7f92fdded58`)
- **Estado general:** `COMPLETE`

## Casos ejecutados

- `last_admin_race` -> `passed=True` ({'name': 'last_admin_race', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'ValidationError'}], 'active_admins': 1, 'passed': True})
- `duplicate_email_race` -> `passed=True` ({'name': 'duplicate_email_race', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'ValidationError'}], 'normalized_count': 1, 'passed': True})
- `open_shift_vs_role_change` -> `passed=True` ({'name': 'open_shift_vs_role_change', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'ValidationError'}], 'role': 'VENDEDOR', 'open_shifts': 1, 'passed': True})
- `lockout_preservation_pg` -> `passed=True` ({'name': 'lockout_preservation_pg', 'lock_survives_reactivate_and_rename': True, 'passed': True})
- `logout_atomic_pg` -> `passed=True` ({'name': 'logout_atomic_pg', 'draft_kept_on_rollback': True, 'audit_unchanged_on_rollback': True, 'commit_status': 302, 'draft_deleted_on_commit': True, 'audit_created_on_commit': True, 'passed': True})
