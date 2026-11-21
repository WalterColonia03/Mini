# Evidencia — S2-USR02-AUTO · HU-USR-02

**HU:** HU-USR-02 · Crear nuevo empleado  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN crea empleado válido y es redirigido a la lista | `EmployeeManagementTests.test_admin_creates_employee_successfully` | ✅ ok |
| CA-2: Correo duplicado es rechazado sin crear segunda cuenta | `EmployeeManagementTests.test_duplicate_email_is_rejected` | ✅ ok |
| CA-3: Rol no-ADMIN recibe 403 y no crea cuenta | `EmployeeManagementTests.test_non_admin_post_is_forbidden` | ✅ ok |

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

**Completada ✅** — Service `create_employee()`, `EmployeeCreationForm` y vista `employee_create`. Template `identity/employee_form.html`. URL `/empleados/nuevo/`. Validación de correo duplicado con normalización.

