# Evidencia — S2-USR01-AUTO · HU-USR-01

**HU:** HU-USR-01 · Lista de empleados  
**Responsable:** Walter Luis Colonia Infantas (D5)  
**Estado:** Completada

## Suite automatizada — cobertura de criterios de aceptación

| CA | Prueba | Resultado |
|---|---|---|
| CA-1: ADMIN puede ver la lista de empleados (HTTP 200) | `EmployeeManagementTests.test_admin_can_see_employee_list` | ✅ ok |
| CA-2: Rol no-ADMIN recibe 403 | `EmployeeManagementTests.test_non_admin_gets_403_on_employee_list` | ✅ ok |

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

**Completada ✅** — Vista `employee_list` con `@roles_required(ADMIN)`. Template `identity/employee_list.html` con nombre, correo, rol y estado activo. URL `/empleados/`.

