# Evidencia — S3-USR04-AUTO · HU-USR-04

**HU:** HU-USR-04 · Desactivar/reactivar cuenta de empleado  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin puede desactivar la cuenta de un empleado activo | `EmployeeEditDeactivateTests.test_admin_can_deactivate_employee` | ✅ ok |
| CA-2: Admin no puede desactivar su propia cuenta (protección) | `EmployeeEditDeactivateTests.test_admin_cannot_deactivate_self` | ✅ ok |
| CA-3: Admin puede reactivar una cuenta previamente inactiva (toggle) | `EmployeeEditDeactivateTests.test_admin_can_reactivate_inactive_employee` | ✅ ok |
| CA-4: Usuario no-admin obtiene 403 al intentar desactivar | `EmployeeEditDeactivateTests.test_non_admin_gets_403_on_deactivate` | ✅ ok |

## Implementación técnica

- **Servicios:** `identity/services.py` → `deactivate_employee(actor, account)`, `reactivate_employee(actor, account)`
- **Vista:** `identity/views.py` → `employee_deactivate(request, account_id)` (toggle automático)
- **URL:** `empleados/<uuid:account_id>/estado/` → `employee-deactivate` (POST only)
- **Plantilla:** botones de acción en `identity/templates/identity/employee_list.html`

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

**Completada ✅** — El administrador puede desactivar o reactivar cualquier cuenta de empleado mediante POST a `/empleados/<uuid>/estado/`. La vista implementa un toggle automático: si la cuenta está activa la desactiva, si está inactiva la reactiva. Se impide que el administrador desactive su propia cuenta activa. El acceso está protegido por `@roles_required(Role.Code.ADMIN)`.

