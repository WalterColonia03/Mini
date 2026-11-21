# Informe de verificación en PostgreSQL 17 · Sublote 02-E (20/11/2026)

- **Motor:** `PostgreSQL 17.10 on x86_64-windows, compiled by msvc-19.44.35226, 64-bit`
- **Puerto usado y cerrado:** `50989` (`port_closed: True`)
- **Base protegida intacta:** `True` (`83e79733798e2e00af2b8f11b7a23aac2b1727d16707d078873d5a36d441bb6c`)
- **Estado general:** `COMPLETE`

## Casos ejecutados

- `last_admin_race` -> `passed=True` ({'name': 'last_admin_race', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'ValidationError'}], 'active_admins': 1, 'passed': True})
- `duplicate_email_race` -> `passed=True` ({'name': 'duplicate_email_race', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'ValidationError'}], 'normalized_count': 1, 'passed': True})
- `open_shift_vs_role_change` -> `passed=True` ({'name': 'open_shift_vs_role_change', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'ValidationError'}], 'role': 'VENDEDOR', 'open_shifts': 1, 'passed': True})
- `lockout_preservation_pg` -> `passed=True` ({'name': 'lockout_preservation_pg', 'lock_survives_reactivate_and_rename': True, 'passed': True})
- `logout_atomic_pg` -> `passed=True` ({'name': 'logout_atomic_pg', 'draft_kept_on_rollback': True, 'audit_unchanged_on_rollback': True, 'commit_status': 302, 'draft_deleted_on_commit': True, 'audit_created_on_commit': True, 'passed': True})
- `role-admin-first-True` -> `passed=True` ({'name': 'role-admin-first-True', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'success'}], 'login_status': [302], 'session_roles': ['ALMACENERO'], 'passed': True})
- `role-admin-first-False` -> `passed=True` ({'name': 'role-admin-first-False', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'success'}], 'login_status': [302], 'session_roles': ['ALMACENERO'], 'passed': True})
- `deactivate-admin-first-True` -> `passed=True` ({'name': 'deactivate-admin-first-True', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'success'}], 'login_status': [200], 'session_roles': [], 'passed': True})
- `deactivate-admin-first-False` -> `passed=True` ({'name': 'deactivate-admin-first-False', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'success'}], 'login_status': [302], 'session_roles': [], 'passed': True})
- `password-admin-first-True` -> `passed=True` ({'name': 'password-admin-first-True', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'success'}], 'login_status': [200], 'session_roles': [], 'passed': True})
- `password-admin-first-False` -> `passed=True` ({'name': 'password-admin-first-False', 'connections': 2, 'postgres_blocking_observed': True, 'results': [{'op': 0, 'result': 'success'}, {'op': 1, 'result': 'success'}], 'login_status': [302], 'session_roles': [], 'passed': True})
