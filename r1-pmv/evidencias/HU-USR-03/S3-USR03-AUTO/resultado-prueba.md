# Evidencia — S3-USR03-AUTO · HU-USR-03

**HU:** HU-USR-03 · Editar datos y rol de empleado  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Sprint:** Sprint 3  
**Estado:** Completada ✅

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: Admin puede ver el formulario de edición precargado con los datos actuales | `EmployeeEditDeactivateTests.test_admin_can_access_employee_edit_form` | ✅ ok |
| CA-2: Admin puede editar el nombre del empleado y los cambios se persisten | `EmployeeEditDeactivateTests.test_admin_can_edit_employee_name` | ✅ ok |
| CA-3: Correo duplicado es rechazado en la edición | `EmployeeEditDeactivateTests.test_duplicate_email_is_rejected_on_edit` | ✅ ok |
| CA-4: Usuario no-admin obtiene 403 al intentar acceder a la edición | `EmployeeEditDeactivateTests.test_non_admin_gets_403_on_edit` | ✅ ok |

## Implementación técnica

- **Servicio:** `identity/services.py` → `update_employee(actor, account, display_name, email, role)`
- **Formulario:** `identity/forms.py` → `EmployeeEditForm`
- **Vista:** `identity/views.py` → `employee_edit(request, account_id)`
- **URL:** `empleados/<uuid:account_id>/editar/` → `employee-edit`
- **Plantilla:** `identity/templates/identity/employee_edit.html`

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

**Completada ✅** — El administrador puede editar nombre, correo electrónico y rol de cualquier empleado a través del formulario en `/empleados/<uuid>/editar/`. Los cambios se persisten atómicamente vía `update_employee()`. La validación rechaza correos ya registrados en otra cuenta. El acceso está protegido por `@roles_required(Role.Code.ADMIN)`.

