# Administración Django y perímetro del inventario 00

El 9 de noviembre de 2026 se comparó el resolver de la configuración aislada con el corte del 5 de noviembre. Coinciden los 106 patrones en orden, nombre y función de destino. El subtotal de negocio es de 41 y el administrativo de 65. La inspección expandió metadatos de Django 5.2.18 con un objeto y un actor en memoria, consultó cero filas, sirvió cero peticiones y dejó las pruebas de acceso administrativo con estado **NO EJECUTADO**, asignadas a la etapa 15. El JSON incluye un registro por patrón y los nombres, tipos, widgets y obligatoriedad de los campos declarados por cada formulario. [Metadatos administrativos](ETAPA-00-admin-metadatos.json)

## Familias de acciones y pantallas

| Patrones | Cantidad | Actor, entrada, acción y salida que describe el código |
|---|---:|---|
| Registros por modelo | 54 | Nueve modelos × seis patrones. Por modelo hay un listado con acciones, alta, historial, confirmación de borrado, ficha de edición/consulta y una redirección heredada a la ficha. Las vistas filtran por permisos técnicos y pueden presentar información en modo de solo lectura. El identificador de objeto es parámetro de ruta. |
| Clave de cuenta desde la ficha de account | 1 | Formulario de personal autorizado para gestionar la clave de una cuenta. Requiere permiso técnico de cambio sobre el objeto. |
| Sitio administrativo | 10 | Índice inicial, ingreso, salida, cambio de clave propia y su confirmación, autocompletado JSON, localización JavaScript, redirección a un objeto, índice por aplicación y resolución final de rutas. Ingreso usa el campo técnico `username` ligado a `Account.USERNAME_FIELD = "email"` y un campo de contraseña. |

El montaje único está en `r1-pmv/config/urls.py:5`. En el Django instalado, `django/contrib/admin/sites.py:202,256,414` define acceso técnico, rutas y login. La puerta administrativa exige `is_active` e `is_staff` para el sitio protegido. Para cada modelo se aplican además los permisos de ver, añadir, modificar y borrar. El superusuario técnico acumula permisos. La identidad de negocio ADMIN, ALMACENERO o VENDEDOR por sí sola no determina ninguno de esos privilegios. La misma instalación utiliza `identity.Account` con `ModelBackend` en `r1-pmv/config/settings.py:59–60`. Un visitante puede llegar al formulario administrativo. La guía 21 documenta la distinción con el bloqueo de la ruta pública de ingreso.

Las plantillas administrativas proceden del framework y se eligen según operación, modelo y permisos. Sus familias principales son login, índice, lista, alta/edición, confirmación de borrado, historial y cambio de clave. Las resoluciones de lista y formulario se encuentran en `django/contrib/admin/options.py:1391,1761,2188,2328` y `django/contrib/auth/admin.py:45,237`. El autocompletado y la traducción JS devuelven recursos técnicos. Los 36 templates propios ya censados corresponden a otra medición del inventario.

## Registros y formularios generados

Las cifras «alta / edición» cuentan los campos de clase al construir el formulario para un actor transitorio con permisos completos. La vista, los fieldsets, el objeto y las relaciones pueden afectar el formulario que recibe un usuario. Cada campo de clase y las columnas, búsquedas, filtros, campos de solo lectura e inlines se listan por nombre en el JSON.

| Modelo | Registro declarado | Campos de clase alta / edición | Salida o relación administrativa |
|---|---|---:|---|
| auth.Group | `django.contrib.auth.admin.GroupAdmin` | 2 / 2 | Grupos y permisos técnicos |
| cash.CashRegister | `r1-pmv/cash/admin.py:7` | 2 / 2 | Código, estado y fecha |
| cash.CashShift | `r1-pmv/cash/admin.py:12` | 4 / 4 | Caja, vendedor, apertura, estado y fecha |
| catalog.Category | `r1-pmv/catalog/admin.py:7` | 2 / 2 | Nombre y estado |
| catalog.Product | `r1-pmv/catalog/admin.py:13` | 7 / 7 | Producto, código, categoría, precio, mínimo y estado |
| identity.Account | `r1-pmv/identity/admin.py:14` | 6 / 10 | Cuenta, rol y estado. Configura privilegios de staff, superusuario, grupo y permisos mediante fieldsets. |
| identity.Role | `r1-pmv/identity/admin.py:8` | 2 / 2 | Código y nombre |
| inventory.InitialInventoryLoad | `r1-pmv/inventory/admin.py:23` | 0 / 0 | Producto, responsable y fecha de solo lectura. Incluye un formulario de lote en línea. |
| inventory.Lot | `r1-pmv/inventory/admin.py:30` | 10 / 10 | Producto, número normalizado, cantidad, costo y vencimiento |

El conjunto de permisos máximos expone la acción declarada `delete_selected` en los nueve registros. Su presentación real depende de permisos y contexto. El inline `inventory.admin.LotInline:6` tiene ocho campos configurados de solo lectura y `can_delete=False`. Los tres formularios técnicos adicionales son `AdminAuthenticationForm`, `PasswordChangeForm` y `AdminPasswordChangeForm`. Para la etapa 15, revisar si el personal técnico debe poder realizar estas operaciones y qué efectos tienen sobre los datos de negocio. Queda pendiente la decisión de alcance con el responsable del sistema. No se ejercieron acciones, permisos ni formularios sobre cuentas persistidas.

## Límite del resolver

En desarrollo, `/static/` se sirve mediante `StaticFilesHandler` al arrancar en modo local con la opción para estáticos. `r1-pmv/config/settings.py:73–74` define su prefijo y directorio. `django/contrib/staticfiles/management/commands/runserver.py:26–35` explica por qué queda fuera de los 106 patrones del URLconf. Los recursos de estilo, iconos y recursos de Django se clasifican como archivos técnicos. Las páginas comunes de error se activan por estado de respuesta. Procesos de gestión, migraciones, tests y tareas de despliegue son entradas técnicas del proyecto y se inventarían por archivo, sin añadirles rutas HTTP.

## Reproducción y conciliación del cierre

Desde la raíz, con el entorno de auditoría ya preparado, ejecutar el siguiente comando. El generador comprueba el resolver guardado y luego escribe exclusivamente su JSON derivado. Una función de guardia rechaza cualquier ejecución SQL en la conexión durante la introspección.

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/inventariar_admin_00.py'
```

El control independiente del índice de planificación contó 82 entradas de historia/idea, 30 reglas y 67 tareas. La matriz de cobertura tiene 219 CA base, de los cuales 41 son de las nueve HU R1 y 178 de HU posteriores. Se suman por separado ocho ideas sin CA y nueve grupos QA que enlazan a 30 afirmaciones históricas. El índice de código contiene 18 formularios propios, 18 modelos propios y 191 métodos de prueba definidos. La verificación de fechas y resultados distingue el inventario inicial y el `check` del 5 de noviembre, las 25 comprobaciones HTTP/persistencia del 9 de noviembre y la presente comparación del resolver. Los recuentos históricos de 03 y de informes anteriores conservan su procedencia.

El cierre del inventario administrativo cubre el conjunto de clases y patrones de este corte. El siguiente caso de esta superficie es SEC-15-01, «login administrativo, staff y permisos de modelo», con cuentas de auditoría dedicadas y autorización de alcance decidida en la etapa correspondiente. El primer caso funcional del siguiente chat sigue siendo HU-AUTH-01/CA-01 en `/`.
