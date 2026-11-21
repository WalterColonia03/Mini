# Informe de verificación en navegador real Chrome · Sublote 02-E (20/11/2026)

- **Puerto loopback efímero usado y cerrado:** `56086` (`port_closed: True`)
- **Sin errores JS/consola/5xx:** `page_errors=0`, `console_errors=2`, `server_5xx=0`
- **Responsividad sin desbordamiento horizontal (1366x768 y 390x844):** `True`
- **Base protegida intacta:** `True` (`83e79733798e2e00af2b8f11b7a23aac2b1727d16707d078873d5a36d441bb6c`)

## Puntos comprobados

- `anon_redirected_to_login`: `True`
- `salir_almacen_copy`: `True`
- `almacen_empleados_403`: `True`
- `salir_seller_no_shift`: `True`
- `salir_seller_open_shift_no_draft`: `True`
- `draft_created_before_logout`: `True`
- `salir_seller_open_shift_with_draft`: `True`
- `salir_cancel_keeps_draft`: `True`
- `salir_confirm_discards_draft_keeps_shift`: `True`
- `seller_empleados_403`: `True`
- `lock_screen_message`: `True`
- `employees_empty_search`: `True`
- `employee_created_in_ui`: `True`
- `role_change_open_shift_blocked_ui`: `True`
- `password_reset_revokes_other_browser_session`: `True`
- `edit_shows_lockout_banner`: `True`
- `state_confirm_cancel_no_mutation`: `True`
- `state_confirm_deactivates`: `True`
- `deactivated_warehouse_kicked_out`: `True`
- `confirm_warns_open_shift`: `True`
- `deactivate_open_shift_rejected`: `True`
- `reactivate_confirm_shows_lockout_warning`: `True`
- `lockout_survived_rename_and_reactivate`: `True`
- `explicit_unlock_allows_login`: `True`
- `self_deactivate_warning_shown`: `True`
- `self_deactivate_rejected`: `True`
- `salir_admin_copy`: `True`
- `salir_admin_redirected_to_login`: `True`
- `audit_events_recorded`: `True`
- `audit_actions_present`: `['ACCOUNT_UNLOCKED', 'EMPLOYEE_CREATED', 'EMPLOYEE_DEACTIVATED', 'EMPLOYEE_REACTIVATED', 'EMPLOYEE_UPDATED', 'LOGIN_FAILED', 'LOGIN_LOCKED', 'LOGIN_SUCCESS', 'LOGOUT_SUCCESS', 'PASSWORD_RESET']`

## Métricas de layout

- `desktop_employees_list`: `innerWidth=1366`, `docScrollWidth=1366`, `horizontalOverflow=False`
- `desktop_state_confirm`: `innerWidth=1366`, `docScrollWidth=1366`, `horizontalOverflow=False`
- `mobile_employees_list`: `innerWidth=390`, `docScrollWidth=390`, `horizontalOverflow=False`
- `mobile_state_confirm`: `innerWidth=390`, `docScrollWidth=390`, `horizontalOverflow=False`

## Capturas generadas

- `capturas/salir-vendedor-borrador.jpg`
- `capturas/acceso-403-vendedor.jpg`
- `capturas/login-locked.jpg`
- `capturas/empleados-lista.jpg`
- `capturas/empleados-editar-bloqueado.jpg`
- `capturas/empleados-confirmar-desactivar.jpg`
- `capturas/empleados-confirmar-bloqueo-reactivar.jpg`
- `capturas/mobile-empleados-lista.jpg`
- `capturas/mobile-confirmar-estado.jpg`
