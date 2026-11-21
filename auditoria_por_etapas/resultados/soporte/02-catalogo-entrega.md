# Catálogo de textos del recorrido de sesión y personal · 20/11/2026

Los grupos siguientes fijan la redacción de las pantallas del tramo para HU-AUTH-03 y HU-USR-01..05. El contrato transversal CT-COHERENCIA-UI cubre la navegación compartida. Cada línea de los bloques es una salida o control. El texto visible conserva tildes, puntuación y mayúsculas. El ajuste de línea de HTML es libre. Las variables de cuenta se escapan como texto. Por ejemplo, {nombre} = Ana García, {correo} = ana@example.invalid, {rol} = Almacenero, {estado} = Activo, {hasta} = 20/11/2026 16:05 (hora de Lima). Un nombre admite homónimos y 120 caracteres. El correo admite 254 después de recortar extremos.

## Salida · CP-HU-AUTH-03-001/002 · tres roles · GET/POST /salir/

```text
Cerrar sesión · Minimarket
Sesión de trabajo
¿Deseas cerrar sesión?
Cerrar sesión
Cancelar
```

Con borrador, con turno sin borrador, vendedor sin turno y rol sin caja, respectivamente:

```text
La venta en preparación se descartará. El turno abierto seguirá ligado a tu cuenta.
Volverás a la pantalla de ingreso. Cualquier venta en preparación abierta se descartará al confirmar y tu turno abierto seguirá ligado a tu cuenta.
Volverás a la pantalla de ingreso. Cualquier venta en preparación abierta se descartará al confirmar; actualmente no tienes un turno de caja abierto.
Volverás a la pantalla de ingreso. Tu cuenta no opera turnos de caja.
```

## Lista · CP-HU-USR-01-001 · ADMIN · GET /empleados/

```text
Empleados
+ Nuevo empleado
Buscar por nombre o correo
Ej.: Ana o ventas@minimarket.local
Buscar
Limpiar
Nombre
Correo
Rol
Estado
Acciones
Activo
Inactivo
Editar
Desactivar
Reactivar
No se encontraron empleados para el criterio ingresado.
No hay empleados registrados.
```

La fila muestra {nombre}, {correo}, {rol} y {estado}. Limpiar requiere búsqueda. El cambio de estado corresponde a cuentas ajenas. El vacío sin filtro es una rama de presentación excepcional porque ADMIN figura en la lista ordinaria.

## Alta y edición · CP-HU-USR-02-001/002 y CP-HU-USR-03-001/002 · ADMIN

```text
Nuevo empleado
Editar empleado
Nombre completo
Ej.: Ana García
Correo de trabajo
ana@empresa.com
Contraseña inicial
Mínimo 7 caracteres, con al menos una mayúscula, una minúscula y un número.
Rol
— Seleccionar rol —
Administrador
Almacenero
Vendedor
Crear empleado
Guardar cambios
Cancelar
{nombre} · {estado}
Nueva contraseña (opcional)
Déjelo en blanco si no desea cambiar la contraseña actual. Si ingresa una nueva, debe tener al menos 7 caracteres, mayúscula, minúscula y número.
Desbloquear cuenta explícitamente (reiniciar bloqueo por intentos fallidos)
Marca esta opción únicamente para levantar manualmente un bloqueo temporal vigente.
Cuenta con bloqueo temporal vigente por intentos fallidos (hasta {hasta}). Renombrar el correo o reactivar la cuenta conserva este bloqueo; marca «Desbloquear cuenta explícitamente» para levantarlo de forma auditada.
Empleado «{nombre}» creado correctamente.
Empleado «{nombre}» actualizado.
```

La clave inicial solo aparece en alta. El reemplazo y el desbloqueo son opcionales en edición. Conservar los mensajes de validación por campo de Django en es-pe, los límites inclusivos y el catálogo de ingreso de etapa 01. Mensajes propios de personal:

```text
Este campo es obligatorio.
Introduzca una dirección de correo electrónico válida.
Los caracteres nulos no están permitidos.
Asegúrese de que este valor tenga como máximo {máximo} caracteres (tiene {longitud}).
El correo ya está registrado.
Ingrese una contraseña inicial.
Seleccione un rol para el empleado.
Seleccione un rol válido de la lista.
Seleccione un rol válido del minimarket.
La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.
La nueva contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.
La contraseña elegida es demasiado débil o predecible. Combine letras y números distintos.
No puedes cambiar el rol de tu propia cuenta.
No se puede cambiar el rol del único administrador activo.
No se puede cambiar el rol de un empleado con un turno de caja abierto. Cierre el turno primero.
```

## Confirmación y resultado · CP-HU-USR-04-001, CP-HU-USR-05-001 y CP-DOC-02-04-001 · ADMIN

```text
Confirmar cambio de estado · Empleados · Minimarket
Personal · Confirmación de estado
Confirmar desactivación de empleado
Confirmar reactivación de empleado
Volver a empleados
Nombre completo
Correo
Rol
Estado actual
Acción solicitada
Desactivar cuenta
Reactivar cuenta
Bloqueo temporal por intentos fallidos
Vigente (se conserva hasta expirar o desbloqueo explícito)
Sin bloqueo vigente
La cuenta de «{nombre}» ya tiene el estado solicitado. No se aplicarán cambios.
Volver al listado
La cuenta seguirá activa y conservará sus sesiones.
Al confirmar la desactivación, se cerrarán de inmediato todas las sesiones activas de esta cuenta y se impedirá cualquier nuevo ingreso. Los registros históricos (ventas, cierres de caja, actas y cargas) se conservarán intactos.
Restricción: No puedes desactivar tu propia cuenta de administrador.
Restricción: Es el último administrador activo; el sistema rechazará dejar cero administradores activos.
Turno de caja abierto: El vendedor tiene un turno abierto actualmente; no se permitirá desactivar la cuenta hasta cerrar su turno.
Al confirmar la reactivación, la cuenta volverá a quedar activa con su correo, rol y contraseña vigentes.
Bloqueo temporal vigente: La reactivación no levanta el bloqueo por intentos fallidos; permanecerá vigente hasta vencer o ser desbloqueado explícitamente en «Editar».
Confirmar desactivación
Confirmar reactivación
Cancelar
Seleccione una acción de estado válida.
Cuenta de «{nombre}» desactivada.
Cuenta de «{nombre}» reactivada.
La cuenta de «{nombre}» ya tiene el estado solicitado.
No puedes desactivar tu propia cuenta.
No se puede desactivar al único administrador activo.
No se puede desactivar a un vendedor con un turno de caja abierto. Cierre el turno primero.
Correo o contraseña incorrectos
```

Cada advertencia requiere comprobar su condición. En POST prevalece el estado actual del servidor. La decisión sobre personal no aplica un aporte, no autoriza un reintegro y no cambia titular ni saldo de caja.

Para el error de longitud, {máximo} es 120 o 254 y {longitud} es la cantidad de caracteres recibidos después de recortar los extremos. Un nombre de 121 y un correo de 255 se rechazan. Las salidas defensivas sin camino normal de interfaz conservan su clasificación en el informe.
