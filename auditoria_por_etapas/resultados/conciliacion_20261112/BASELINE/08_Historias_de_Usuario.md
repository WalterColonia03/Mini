# 8. Historias de usuario

> **Actualización 05/11/2026:** Catálogo de requisitos, incluidas historias futuras o fuera del alcance; no es una lista de funcionalidades ya entregadas. Consulte la guía actual para las discrepancias identificadas. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Nota de lectura:** Este documento reúne las historias de usuario del sistema de la bodega. El orden de atención, la prioridad, los Story Points, las dependencias y la asignación a Sprint se consultan de forma exclusiva en el Product Backlog (`09_Product_Backlog.md`).

---

## 8.1 EPIC-SEG — Ingreso y personal (13 HUs · 44 SP)

---

### HU-AUTH-01 · Ingresar con mi cuenta de trabajo
- **Épica:** Ingreso y personal
- **Historia:** Como empleado de la bodega, quiero ingresar con mi correo y contraseña de trabajo, para acceder a las opciones de mi puesto y proteger la información del negocio.
- **Reglas de negocio:** RN-29
- **Criterios de aceptación:**
  1. Dado que tengo una cuenta activa con uno de los roles exclusivos `ADMIN`, `ALMACENERO` o `VENDEDOR`, cuando ingreso mi correo y contraseña correctos, entonces el sistema crea mi sesión y me conduce a las opciones autorizadas para ese único rol (RN-29).
  2. Dado que ingreso una contraseña incorrecta o un correo no registrado, cuando el sistema lo valida, entonces muestra el mensaje general «Correo o contraseña incorrectos» sin indicar cuál de los dos datos falló.
  3. Dado que mi cuenta de empleado está inactiva, cuando ingreso credenciales correctas, entonces el sistema rechaza el acceso con el mismo mensaje general «Correo o contraseña incorrectos» sin dar información sobre el estado de la cuenta.
  4. Dado que inicié sesión, cuando intento abrir por URL o solicitud directa una operación que RN-29 no permite a mi rol, entonces el sistema deniega el acceso, no expone los datos de esa operación y no modifica información.

---

### HU-AUTH-02 · Autenticación — Bloquear cuenta por intentos fallidos
- **Épica:** Ingreso y personal
- **Historia:** Como empleado o administrador, quiero que las cuentas se bloqueen temporalmente tras reiterados intentos fallidos de acceso, para proteger los accesos y las operaciones de la bodega.
- **Reglas de negocio:** RN-17
- **Criterios de aceptación:**
  1. Dado que un usuario ingresa una contraseña incorrecta por quinta vez consecutiva, cuando se procesa el quinto intento fallido, entonces el sistema bloquea temporalmente la cuenta por 15 minutos conforme a la regla RN-17.
  2. Dado que la cuenta se encuentra bajo bloqueo temporal, cuando se intenta ingresar nuevamente con cualquier clave, entonces el sistema impide el acceso y muestra en pantalla los minutos restantes del bloqueo.
  3. Dado que transcurrió el tiempo de espera de 15 minutos, cuando el empleado ingresa sus credenciales válidas, entonces el sistema le permite ingresar exitosamente y restablece el contador de intentos a cero.

---

### HU-AUTH-03 · Salir de mi cuenta al terminar
- **Épica:** Ingreso y personal
- **Historia:** Como empleado de la bodega, quiero salir de mi cuenta al terminar mi labor o ausentarme, para asegurar que nadie use mi sesión ni opere la caja en mi nombre.
- **Reglas de negocio:** RN-29, RN-30
- **Criterios de aceptación:**
  1. Dado que tengo una sesión sin una venta en preparación, cuando elijo «Salir» y confirmo la advertencia de que un turno abierto seguirá ligado a mi usuario, entonces el sistema invalida la sesión y regresa a la pantalla de ingreso sin cerrar ese turno (RN-30).
  2. Dado que mi venta en preparación contiene al menos una línea, cuando elijo «Salir», entonces el sistema advierte que descartará la venta; si confirmo, elimina todas las líneas sin afectar caja ni existencias y cierra la sesión, y si cancelo, conserva tanto la sesión como la venta (RN-30).
  3. Dado que la salida fue confirmada, cuando se usa el botón Atrás o una URL anterior, entonces no se ve información del empleado ni se ejecutan operaciones sin autenticarse; si el mismo vendedor vuelve a ingresar, conserva su turno abierto pero no el borrador descartado, y otro vendedor no puede usar ni reemplazar ese turno.

---

### HU-AUTH-04a · Autenticación — Cerrar automáticamente la sesión previa
- **Épica:** Ingreso y personal
- **Historia:** Como empleado, quiero que al iniciar sesión en un nuevo equipo se cierre automáticamente mi sesión anterior, para trabajar en un solo puesto a la vez y no dejar accesos abiertos.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que tengo una sesión abierta en un equipo, cuando inicio sesión desde otro equipo con mis credenciales válidas, entonces la sesión previa se cierra de inmediato y solo queda habilitado el nuevo puesto.
  2. Dado que mi sesión previa fue cerrada por inicio en otro equipo, cuando intento realizar cualquier acción desde ese puesto anterior, entonces la pantalla se bloquea y muestra «La sesión fue abierta en otro dispositivo».
  3. Dado que la pantalla fue bloqueada, cuando intento interactuar con el puesto anterior, entonces el sistema me redirige a la pantalla de ingreso exigiendo escribir las credenciales.

---

### HU-AUTH-04b · Autenticación — Descartar venta sin confirmar al cerrarse la sesión
- **Épica:** Ingreso y personal
- **Historia:** Como vendedor, quiero que una venta sin confirmar se descarte si mi sesión se cierra por inicio en otro equipo, para que no queden cobros a medias ni se alteren las existencias o la caja.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que tengo una venta en curso sin confirmar y mi sesión se cierra por inicio en otro equipo, cuando se procesa el cierre automático, entonces la venta incompleta se descarta y la lista de venta se libera.
  2. Dado que se descarta una venta incompleta por cierre de sesión, cuando consulto las existencias de productos y el dinero en caja, entonces ambos permanecen iguales a su estado previo sin alteraciones.

---

### HU-AUTH-05 · Autenticación — Recuperar contraseña por correo
- **Épica:** Ingreso y personal
- **Historia:** Como empleado, quiero recibir un código temporal en mi correo al olvidar mi clave, para restablecer mi acceso al sistema de forma segura sin depender de un administrador.
- **Reglas de negocio:** RN-17, RN-18, RN-24
- **Criterios de aceptación:**
  1. Dado que olvidé mi contraseña, cuando ingreso mi correo registrado en el formulario de recuperación, entonces el sistema despacha un código numérico temporal de 4 dígitos con validez de 15 minutos (RN-18).
  2. Dado que recibí el código temporal, cuando lo ingreso dentro del tiempo de validez, entonces el sistema me permite definir una nueva contraseña que cumpla con los requisitos de seguridad de al menos 7 caracteres con mayúscula, minúscula y número (RN-24).
  3. Dado que el código temporal fue utilizado exitosamente para cambiar la contraseña, cuando se intenta utilizar nuevamente el mismo código, entonces el sistema lo rechaza por haber expirado su único uso permitido (RN-18).
  4. Dado que han transcurrido más de 15 minutos desde su emisión, cuando ingreso el código, entonces el sistema muestra el mensaje «El código ha caducado» y solicita generar uno nuevo.
  5. Dado que una recuperación acumula 5 códigos erróneos consecutivos, cuando se intenta otro código, entonces el sistema suspende ese flujo durante 15 minutos sin bloquear por ello una sesión ya autenticada ni revelar si el correo existe (RN-17).

---

### HU-USR-01 · Usuarios — Listar empleados del sistema
- **Épica:** Ingreso y personal
- **Historia:** Como administrador o dueño, quiero ver la lista de todos los empleados registrados con su estado y rol, para supervisar quién tiene acceso activo al sistema.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo a la sección de empleados, cuando la lista carga, entonces veo el nombre, correo, rol y estado (activo/inactivo) de cada empleado registrado.
  2. Dado que la lista está cargada, cuando busco por nombre o correo, entonces el sistema filtra los resultados y muestra solo los empleados que coinciden.
  3. Dado que la lista tiene varios registros, cuando la exploro, entonces puedo distinguir claramente cuáles cuentas están activas y cuáles inactivas.

---

### HU-USR-02 · Usuarios — Crear cuenta de nuevo empleado
- **Épica:** Ingreso y personal
- **Historia:** Como administrador, quiero registrar la cuenta de un nuevo trabajador con su correo único, rol y contraseña inicial, para permitir que el nuevo empleado acceda al sistema.
- **Reglas de negocio:** RN-12, RN-24
- **Criterios de aceptación:**
  1. Dado que completo el formulario de nuevo empleado con nombre, correo, rol y contraseña inicial válida, cuando guardo el registro, entonces el empleado queda activo y puede iniciar sesión con esas credenciales.
  2. Dado que ingreso un correo que ya existe en el sistema (activo o inactivo), cuando intento guardar, entonces el sistema muestra «El correo ya está registrado» y no permite duplicados (RN-12).
  3. Dado que ingreso una contraseña inicial, cuando la valido, entonces el sistema verifica que tenga al menos 7 caracteres con mayúsculas, minúsculas y números, y rechaza la contraseña si no cumple ese criterio (RN-24).
  4. Dado que el empleado fue creado, cuando finaliza el registro, entonces el sistema confirma su nombre, correo, estado activo y rol asignado.

---

### HU-USR-03 · Usuarios — Editar datos y rol de un empleado
- **Épica:** Ingreso y personal
- **Historia:** Como administrador, quiero modificar los datos personales y el rol asignado a un empleado, para mantener actualizado el directorio del personal y sus permisos de trabajo.
- **Reglas de negocio:** RN-12
- **Criterios de aceptación:**
  1. Dado que selecciono un empleado registrado, cuando accedo al formulario de edición, entonces puedo modificar sus nombres, apellidos, correo electrónico y su rol de trabajo en el sistema.
  2. Dado que modifico el correo electrónico del empleado, cuando intento guardar, entonces el sistema valida que el nuevo correo no se encuentre registrado previamente por otro trabajador (RN-12).
  3. Dado que cambio el rol del empleado, cuando confirmo la modificación, entonces el nuevo rol queda registrado y aplica de inmediato.

---

### HU-USR-04 · Usuarios — Desactivar cuenta de empleado
- **Épica:** Ingreso y personal
- **Historia:** Como administrador, quiero desactivar la cuenta de un empleado que ya no trabaja en la bodega, para impedir su acceso al sistema.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que selecciono desactivar la cuenta de un empleado activo, cuando confirmo la acción, entonces el empleado queda con estado Inactivo y no puede ingresar al sistema.
  2. Dado que una cuenta de empleado fue desactivada, cuando intenta ingresar al sistema, entonces el sistema muestra el mismo mensaje general «Correo o contraseña incorrectos» que en HU-AUTH-01, sin revelar el estado de la cuenta.
  3. Dado que desactivé una cuenta, cuando la busco en la lista, entonces aparece con estado Inactivo y el historial de operaciones del empleado se conserva.

---

### HU-USR-05 · Usuarios — Reactivar cuenta de empleado
- **Épica:** Ingreso y personal
- **Historia:** Como administrador, quiero reactivar la cuenta de un empleado que regresó al negocio, para restaurar su acceso sin necesidad de crear una cuenta nueva.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que selecciono reactivar la cuenta de un empleado inactivo, cuando confirmo la acción, entonces la cuenta queda con estado Activo y puede ingresar con sus credenciales habituales.
  2. Dado que reactivé una cuenta, cuando el empleado ingresa, entonces accede al sistema con el mismo rol y permisos que tenía antes de la desactivación.

---

### HU-USR-06 · Usuarios — Forzar cierre de sesión remoto
- **Épica:** Ingreso y personal
- **Historia:** Como administrador, quiero cerrar de forma remota la sesión activa de cualquier empleado, para proteger el sistema ante situaciones imprevistas o abandono de puesto.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que un empleado tiene sesión abierta, cuando selecciono «Cerrar sesión» desde la pantalla de administración, entonces el empleado es desconectado de forma inmediata.
  2. Dado que su sesión fue cerrada remotamente, cuando el empleado intenta continuar navegando, entonces el sistema le muestra la pantalla de ingreso con el mensaje «Tu sesión fue cerrada por el administrador».

---

### HU-LOG-01 · Supervisión de accesos – Consultar registro de accesos
- **Épica:** Ingreso y personal
- **Historia:** Como administrador o dueño, quiero consultar el historial de ingresos y salidas del sistema de todos los empleados, para supervisar los accesos y detectar actividad inusual.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al registro de accesos, cuando la lista carga, entonces veo por cada evento: nombre del empleado, tipo de evento (ingreso o salida) y fecha con hora exacta.
  2. Dado que consulto el registro, cuando filtro por empleado o por rango de fechas, entonces el sistema muestra únicamente los eventos que coinciden con el filtro.
  3. Dado que ocurrió un bloqueo de cuenta por intentos fallidos, cuando lo busco en el registro, entonces aparece como un evento diferenciado.

---

## 8.2 EPIC-CAT — Productos y proveedores (14 HUs · 36 SP)

---

### HU-CAT-01 · Categorías — Ver lista de categorías de productos
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero ver la lista completa de categorías registradas, para conocer cómo está organizado el catálogo antes de registrar o modificar productos.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo a la sección de categorías, cuando la lista carga, entonces veo el nombre de cada categoría registrada.
  2. Dado que no hay ninguna categoría registrada, cuando accedo a la sección, entonces el sistema muestra un mensaje indicando que la lista está vacía.

---

### HU-CAT-02 · Categorías — Crear nueva categoría de productos
- **Épica:** Productos y proveedores
- **Historia:** Como administrador de la bodega, quiero registrar una nueva categoría de productos, para organizar los artículos y facilitar su localización en el inventario.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que ingreso un nombre de categoría no vacío, cuando confirmo el registro, entonces el sistema retira espacios sobrantes, guarda la categoría con estado activo y la deja disponible para usos posteriores en el catálogo.
  2. Dado que ya existe una categoría registrada con el mismo nombre aunque cambien mayúsculas o espacios, cuando intento guardar, entonces el sistema muestra el mensaje «La categoría ya existe» y no crea un duplicado.
  3. Dado que el nombre queda vacío al retirar espacios, cuando intento guardar, entonces el sistema indica «El nombre es obligatorio» y no registra la categoría.

---

### HU-CAT-03 · Categorías — Editar nombre de categoría
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero modificar el nombre de una categoría registrada, para corregir errores de escritura o actualizar su denominación.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que edito el nombre de una categoría con un texto nuevo y único, cuando guardo, entonces el cambio se refleja en la lista y en todos los productos pertenecientes a ella.
  2. Dado que edito el nombre con una denominación que ya pertenece a otra categoría, cuando intento guardar, entonces el sistema muestra «La categoría ya existe» y no realiza el cambio.

---

### HU-CAT-04 · Categorías — Eliminar categoría sin productos
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero eliminar una categoría que no tiene productos asociados, para mantener el catálogo limpio y sin grupos vacíos.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que selecciono eliminar una categoría que no tiene productos asociados, cuando confirmo la acción, entonces la categoría desaparece de la lista.
  2. Dado que selecciono eliminar una categoría que tiene productos vinculados, cuando intento confirmar, entonces el sistema muestra «No se puede eliminar: esta categoría tiene productos registrados» y cancela la acción.

---

### HU-PROD-01 · Productos — Ver catálogo completo de productos
- **Épica:** Productos y proveedores
- **Historia:** Como administrador o almacenero, quiero ver la lista completa de productos registrados con su precio y existencias, para conocer la disponibilidad de cada artículo antes de operar. El vendedor consulta productos únicamente en su flujo de venta autorizado (RN-29; conciliación DOC-00-14, 09/11/2026).
- **Reglas de negocio:** RN-06
- **Criterios de aceptación:**
  1. Dado que accedo al catálogo de productos, cuando la lista carga, entonces veo por cada artículo: nombre, código de barras, categoría, precio de venta y existencias disponibles.
  2. Dado que consulto el catálogo, cuando busco por nombre o código de barras, entonces el sistema filtra los resultados y muestra solo los artículos coincidentes.
  3. Dado que un producto tiene existencias iguales o inferiores al mínimo configurado (RN-06), cuando aparece en la lista, entonces muestra una señal visual de alerta.

---

### HU-PROD-02 · Registrar un producto por unidad con vencimiento
- **Épica:** Productos y proveedores
- **Historia:** Como administrador de la bodega, quiero registrar un producto de cualquier categoría activa, por unidad y con vencimiento obligatorio, para incorporarlo al catálogo y controlar sus existencias (alcance actual aceptado en DOC03-01, 09/11/2026).
- **Reglas de negocio:** RN-06, RN-27, RN-29
- **Criterios de aceptación:**
  1. Dado que ingreso con rol `ADMIN` y existe una categoría activa, cuando la elijo y registro nombre único ignorando mayúsculas y espacios redundantes, código de barras, unidad `UND`, precio con IGV incluido y cantidad mínima válidos, entonces el producto queda asociado a esa categoría, sea o no de enlatados, y con control de vencimiento obligatorio; una categoría inactiva o inexistente se rechaza sin crear producto (RN-03, RN-29; DOC03-01, 09/11/2026).
  2. Dado que registro el precio de venta en soles, cuando el sistema lo valida, entonces exige un valor mayor que cero con máximo dos decimales y lo interpreta como precio final con IGV incluido (RN-27).
  3. Dado que indico un código de barras que ya pertenece a otro producto, cuando intento guardar, entonces el sistema rechaza el registro por ser un código irrepetible.
  4. Dado que indico la cantidad mínima de existencias, cuando guardo, entonces acepta un entero entre 0 y 999999 inclusive, tanto en formulario como en servidor; si no ingreso el campo al registrar, almacena 10. Un valor fuera del rango se rechaza sin guardar cambios, sin exigir todavía una alerta visual en Sprint 1 (RN-06; PROP-03C-LIMITES aceptada, 10/11/2026).
  5. Dado que todos los datos son válidos, cuando se confirma el registro, entonces el producto se crea con cero existencias y no resulta vendible hasta recibir lotes; si un `ALMACENERO` o `VENDEDOR` intenta registrar por acceso directo, el sistema deniega la operación y no crea ningún producto (RN-29).

---

### HU-PROD-03 · Productos — Escanear código de barras para registrar producto
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero capturar el código de barras de un producto nuevo con el lector, para registrar su código en el formulario de forma rápida y sin errores de digitación.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que abro «Escanear código» en el alta de producto, cuando leo una etiqueta, entonces «Código leído» muestra automáticamente el valor temporal. Al pulsar «Usar código», se copia a la ficha para confirmarlo con «Registrar producto».
  2. Dado que el código leído ya existe en el catálogo, cuando se detecta la lectura, entonces el sistema advierte «El código de barras ya está registrado» e impide duplicarlo.

---

### HU-PROD-04 · Productos — Editar datos de un producto
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero modificar el nombre, código de barras, precio, categoría o cantidad mínima de un producto registrado, para mantener actualizada la información de los artículos (corrección de código aceptada en DOC03-02, 09/11/2026).
- **Reglas de negocio:** RN-06
- **Criterios de aceptación:**
  1. Dado que edito el precio de venta de un producto, cuando guardo, entonces el nuevo precio aplica a las ventas registradas a partir de ese momento; las ventas pasadas conservan el precio cobrado.
  2. Dado que edito la cantidad mínima de un producto, cuando guardo, entonces el umbral de alerta se actualiza de inmediato (RN-06).
  3. Dado que ingreso como `ADMIN`, cuando corrijo el código de barras de un producto, entonces se exige un código normalizado único, se conserva la identidad del producto y sus referencias, y las ventas pasadas mantienen sus datos históricos; un código duplicado o inválido se rechaza sin guardar cambios (DOC03-02, decisión del usuario del 09/11/2026; RN-28, RN-29).
  4. Dado que edito el nombre de un producto con una descripción válida, cuando guardo, entonces el nuevo nombre se actualiza en el catálogo y en la pantalla de venta; debe ser único entre productos activos e inactivos, ignorando mayúsculas y espacios redundantes, y conserva los datos de ventas pasadas. Un duplicado se rechaza sin guardar ningún cambio; marca, contenido o presentación distinguen productos diferentes (PROP-03C-NOMBRE aceptada, 10/11/2026).
  5. Dado que reasigno la categoría de un producto, cuando confirmo el cambio, entonces el producto queda reclasificado en la nueva categoría.

---

### HU-PROD-05 · Productos — Gestionar estado de disponibilidad comercial
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero cambiar el estado de un producto entre Activo e Inactivo, para suspender temporalmente su venta sin borrarlo o volver a habilitarlo.
- **Reglas de negocio:** RN-03 para existencias vigentes y RN-29 para los permisos de cada rol.
- **Criterios de aceptación:**
  1. Dado que cambio el estado de un producto a «Inactivo», cuando un vendedor intenta buscarlo en mostrador, entonces el producto queda excluido de la venta.
  2. Dado que el administrador reactiva un producto, cuando el vendedor con turno propio abierto lo busca en mostrador, entonces aparece con su precio de venta actual y la suma de unidades de lotes vigentes si la categoría está activa y esa suma es positiva. Solo cuentan los lotes que vencen después de hoy en Lima (RN-03). Con categoría desactivada o cero unidades vigentes, la ficha queda activa, el catálogo indica el motivo y el mostrador la excluye.
  3. Dado que un producto se encuentra inactivo, cuando el administrador revisa el catálogo, entonces se muestra con la etiqueta «Inactivo» y conserva todo su historial.

---

### HU-PROD-06 · Productos — Consultar vencimientos de productos
- **Épica:** Productos y proveedores
- **Historia:** Como administrador o encargado del almacén, quiero consultar la lista de productos cuyos lotes vencen próximamente, para tomar decisiones de baja o rotación antes de que caduquen.
- **Reglas de negocio:** RN-03
- **Criterios de aceptación:**
  1. Dado que accedo a la consulta de vencimientos, cuando la lista carga, entonces veo los productos ordenados de menor a mayor días restantes de vida útil, mostrando nombre, número de lote y fecha de caducidad.
  2. Dado que un lote ya venció por tener fecha igual o anterior a hoy según la hora de Lima, cuando aparece en la lista, entonces figura marcado como «Vencido» y bloqueado para venta (RN-03).
  3. Dado que consulto la lista, cuando filtro por número de días (por ejemplo próximos 7 días), entonces solo aparecen los lotes cuyo vencimiento se ubica dentro de ese plazo.

---

### HU-PROV-01 · Proveedores — Ver lista de proveedores
- **Épica:** Productos y proveedores
- **Historia:** Como administrador o encargado del almacén, quiero ver la lista de todos los proveedores registrados con su estado, para conocer los contactos disponibles para pedidos de mercadería.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo a la sección de proveedores, cuando la lista carga, entonces veo el nombre comercial, RUC y estado (activo/inactivo) de cada proveedor.
  2. Dado que busco por nombre o RUC, cuando el sistema filtra, entonces muestra únicamente los proveedores que coinciden.

---

### HU-PROV-02 · Proveedores — Registrar nuevo proveedor
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero registrar un nuevo proveedor con su nombre, RUC y teléfono, para asociarlo a las entradas de mercadería y solicitudes de compra.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que completo el formulario con nombre, RUC y datos de contacto del proveedor, cuando guardo, entonces el proveedor queda registrado con estado Activo y disponible para pedidos.
  2. Dado que ingreso un RUC que ya pertenece a otro proveedor registrado, cuando intento guardar, entonces el sistema muestra «El RUC ya está registrado» y no crea el duplicado.
  3. Dado que omito el RUC o el nombre, cuando intento guardar, entonces el sistema indica los campos obligatorios faltantes y no registra el proveedor.

---

### HU-PROV-03 · Proveedores — Editar datos de un proveedor
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero actualizar el nombre, RUC o teléfono de un proveedor, para mantener vigentes sus datos comerciales.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que edito los datos de contacto de un proveedor, cuando guardo, entonces los cambios se reflejan de inmediato.
  2. Dado que edito el RUC de un proveedor con un valor que ya pertenece a otro, cuando intento guardar, entonces el sistema advierte que el RUC ya existe y no guarda el cambio.

---

### HU-PROV-04 · Proveedores — Gestionar estado de vigencia del proveedor
- **Épica:** Productos y proveedores
- **Historia:** Como administrador, quiero cambiar el estado de un proveedor entre Activo e Inactivo, para pausar pedidos a proveedores sin relación vigente sin perder su historial.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que cambio el estado de un proveedor a «Inactivo», cuando se elabora una solicitud de reposición, entonces el proveedor queda excluido de la lista de selección.
  2. Dado que regreso a un proveedor al estado «Activo», cuando se crea una reposición, entonces vuelve a estar disponible para pedidos.
  3. Dado que un proveedor está inactivo, cuando consulto la lista general, entonces se visualiza claramente como «Inactivo» conservando su historial previo.

---

## 8.3 EPIC-INV — Mercadería y reposición (13 HUs · 41 SP)

---

### HU-INV-01a · Registrar las existencias iniciales por lotes
- **Épica:** Mercadería y reposición
- **Historia:** Como encargado del almacén, quiero ingresar las existencias iniciales de un producto de cualquier categoría activa, por unidad y con vencimiento obligatorio, mediante uno o varios lotes, para tener mercadería disponible para la venta con sus fechas de vencimiento controladas.
- **Reglas de negocio:** RN-01, RN-03, RN-14, RN-19, RN-29
- **Criterios de aceptación:**
  1. Dado que ingreso con rol `ALMACENERO` y el producto aún no tiene una carga inicial confirmada, cuando envío uno o varios lotes válidos, entonces el sistema confirma una única carga directa sin pedido previo; cualquier otro rol recibe una denegación y no altera existencias (RN-01, RN-29).
  2. Dado que completo cada lote, cuando el sistema lo valida, entonces exige un número comercial no vacío que normaliza a mayúsculas y que sea único dentro del producto, una cantidad entera positiva, un costo unitario positivo con máximo cuatro decimales y una fecha de vencimiento posterior a la fecha actual de `America/Lima` (RN-03).
  3. Dado que algún lote es inválido o repetido, o que ya existe o compite simultáneamente otra carga inicial para el producto, cuando intento confirmar, entonces el sistema rechaza toda la operación y no guarda lotes, existencias ni costo; como máximo una carga concurrente puede resultar confirmada (RN-01).
  4. Dado que todos los lotes son válidos, cuando se confirma la carga, entonces las existencias del producto equivalen a la suma de sus cantidades, el producto queda vendible y su costo promedio inicial se obtiene ponderando cantidad por costo, almacenado con cuatro decimales `HALF_UP` y mostrado con dos (RN-14).
  5. Dado que los lotes quedaron guardados, cuando se revisan sus datos, entonces cada uno conserva su número comercial, cantidad disponible, costo, vencimiento, instante de ingreso inmutable y un identificador interno; la futura salida FEFO ordena por vencimiento, instante de ingreso e identificador interno (RN-19).

---

### HU-INV-01b · Inventario — Recalcular el costo promedio en entradas posteriores
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador, quiero que el costo promedio del producto se recalcule al confirmar entradas posteriores a su carga inicial, para que los cálculos de rentabilidad reflejen el valor real pagado sin duplicar el alcance de `HU-INV-01a`.
- **Reglas de negocio:** RN-14
- **Criterios de aceptación:**
  1. Dado que un producto ya completó su carga inicial y tiene existencias previas, cuando se confirma una entrada posterior autorizada con cantidad y costo de compra, entonces el sistema recalcula el costo promedio usando las unidades anteriores y las ingresadas conforme a RN-14.
  2. Dado que consulto el costo promedio después de la entrada, cuando lo comparo con el cálculo ponderado, entonces coincide con el valor almacenado a cuatro decimales y se muestra redondeado a dos, sin alterar costos históricos de ventas anteriores.

---

### HU-INV-02 · Inventario — Registrar baja de inventario por merma
- **Épica:** Mercadería y reposición
- **Historia:** Como encargado del almacén, quiero registrar la baja de productos deteriorados, vencidos o sustraídos indicando su lote y causa reconocida, para retirar mercadería no vendible y justificar la pérdida.
- **Reglas de negocio:** RN-04, RN-05, RN-20
- **Criterios de aceptación:**
  1. Dado que selecciono un lote de producto, cuando indico la cantidad a retirar y la causa (Vencimiento, Daño o rotura, o Robo o faltante), entonces el sistema descuenta las unidades validando que no superen las existencias del lote (RN-04, RN-05).
  2. Dado que el lote ya alcanzó su fecha de vencimiento según la hora de Lima, cuando se intenta registrar una baja, entonces el sistema exige procesarla como Vencimiento e impide registrarla como daño físico conforme a la regla RN-05.
  3. Dado que la causa seleccionada es Daño o rotura o Robo o faltante, cuando se registra la baja, entonces el sistema exige obligatoriamente detallar lo ocurrido e identifica al empleado responsable (RN-20).
  4. Dado que se confirma la baja, cuando termina la operación, entonces el sistema genera una constancia interna de merma con número correlativo, producto, lote, fecha y motivo.

---

### HU-INV-03 · Inventario – Realizar ajuste por conteo físico
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador, quiero registrar ajustes positivos o negativos tras contar físicamente los estantes, para cuadrar las diferencias entre lo contado y el sistema manteniendo el control por lote.
- **Reglas de negocio:** RN-01
- **Criterios de aceptación:**
  1. Dado que el conteo en mostrador revela unidades de más (ajuste positivo), cuando el administrador lo registra, entonces el sistema exige asociarlo a un lote o crear uno nuevo con su fecha de vencimiento.
  2. Dado que el conteo revela unidades de menos (ajuste negativo), cuando el administrador lo registra, entonces el sistema exige indicar de qué lote específico se descuentan las unidades.
  3. Dado que se confirma el ajuste físico, cuando el sistema lo guarda, entonces genera un registro con fecha, cantidad ajustada, empleado responsable y motivo obligatorio.

---

### HU-INV-04 · Mercadería — Consultar movimientos de un producto
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador o encargado del almacén, quiero consultar el historial cronológico de movimientos de un producto, para revisar las entradas, ventas, mermas y ajustes.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que selecciono un producto, cuando consulto sus movimientos, entonces el sistema muestra en orden cronológico todas las entradas, salidas y saldo resultante con fecha, tipo de operación, cantidad y lote.
  2. Dado que un movimiento de entrada nació de una reposición aprobada (HU-SOL-05a), cuando abro el detalle, entonces muestra el proveedor y la referencia de recepción.
  3. Dado que una entrada provino de carga inicial o ajuste, cuando abro el detalle, entonces se etiqueta como carga directa o ajuste con su motivo y responsable.
  4. Dado que aplico filtros por fechas o tipo de movimiento, cuando ejecuto la búsqueda, entonces se visualizan solo las operaciones coincidentes.

---

### HU-INV-05 · Inventario — Consultar historial de bajas
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador o dueño, quiero consultar el historial de todas las bajas de mercadería registradas, para vigilar las pérdidas y analizar sus causas.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al historial de bajas, cuando la lista carga, entonces veo por cada baja: producto, motivo, número de lote, cantidad, empleado que la registró y fecha.
  2. Dado que filtro por motivo o período de tiempo, cuando aplico el filtro, entonces el sistema muestra únicamente las bajas coincidentes.

---

### HU-INV-06 · Inventario — Consultar historial de ajustes
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador o dueño, quiero consultar el historial de ajustes por conteo físico, para verificar las correcciones realizadas en las existencias.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al historial de ajustes, cuando la lista carga, entonces veo por cada ajuste: producto, tipo (positivo o negativo), cantidad ajustada, responsable y fecha.
  2. Dado que filtro por producto o rango de fechas, cuando aplico el filtro, entonces el sistema exhibe los registros correspondientes.

---

### HU-SOL-01 · Reposición – Crear solicitud de reposición
- **Épica:** Mercadería y reposición
- **Historia:** Como encargado del almacén, quiero generar una solicitud de reposición seleccionando productos y un proveedor habitual, para pedir la compra de mercadería al administrador.
- **Reglas de negocio:** RN-06
- **Criterios de aceptación:**
  1. Dado que elaboro una nueva solicitud, cuando elijo un proveedor activo y agrego productos indicando las cantidades requeridas, entonces el sistema crea la solicitud en estado Pendiente.
  2. Dado que agrego artículos con existencias iguales o inferiores a su mínimo configurado —10 solo cuando se conservó el valor predeterminado—, cuando el sistema carga la sugerencia, entonces propone dichos artículos para facilitar el pedido (RN-06).
  3. Dado que intento registrar una solicitud sin productos o con cantidades menores o iguales a cero, cuando intento guardarla, entonces el sistema bloquea el envío y exige ingresar productos válidos.

---

### HU-SOL-02 · Reposición — Listar solicitudes con filtro por estado
- **Épica:** Mercadería y reposición
- **Historia:** Como encargado del almacén o administrador, quiero consultar la lista de solicitudes de reposición filtrando por estado, para hacer seguimiento a los pedidos.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que ingreso a la sección de solicitudes, cuando filtro por estado (Pendiente, Aprobada, Rechazada, Parcialmente atendida o Completada), entonces el sistema muestra con exactitud las solicitudes coincidentes.
  2. Dado que elijo una solicitud, cuando abro su detalle, entonces veo productos pedidos, cantidades, fecha, proveedor y observaciones.
  3. Dado que no existen solicitudes con el estado elegido, cuando filtro, entonces la pantalla informa que no hay registros.

---

### HU-SOL-03 · Reposición — Aprobar solicitud de reposición
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador o dueño, quiero aprobar una solicitud de reposición pudiendo cambiar el proveedor sugerido, para autorizar la compra con las mejores condiciones comerciales.
- **Reglas de negocio:** RN-16
- **Criterios de aceptación:**
  1. Dado que reviso una solicitud en estado Pendiente, cuando la apruebo manteniendo el proveedor sugerido, entonces la solicitud pasa a estado Aprobada con dicho proveedor (RN-16).
  2. Dado que reviso una solicitud en estado Pendiente, cuando selecciono un proveedor alternativo antes de aprobar, entonces la solicitud pasa a estado Aprobada con el proveedor actualizado.
  3. Dado que la solicitud queda aprobada, cuando el encargado del almacén la consulta, entonces visualiza su nuevo estado y el proveedor confirmado.

---

### HU-SOL-04 · Reposición — Rechazar solicitud de reposición
- **Épica:** Mercadería y reposición
- **Historia:** Como administrador o dueño, quiero rechazar una solicitud de reposición indicando el motivo, para comunicar al almacenero la decisión tomada.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que reviso una solicitud Pendiente, cuando intento rechazarla sin escribir un motivo, entonces el sistema muestra «El motivo del rechazo es obligatorio» y no cambia el estado.
  2. Dado que ingreso el motivo y confirmo, cuando el sistema lo procesa, entonces la solicitud pasa a Rechazada y el motivo queda visible para el personal.

---

### HU-SOL-05a · Reposición — Completar la recepción total de una solicitud
- **Épica:** Mercadería y reposición
- **Historia:** Como encargado del almacén, quiero registrar la llegada completa de mercadería de una solicitud aprobada con lote, vencimiento y costo, para ingresar las existencias y actualizar el costo promedio.
- **Reglas de negocio:** RN-01, RN-03, RN-14, RN-19
- **Criterios de aceptación:**
  1. Dado que recibo todos los artículos de una solicitud aprobada, cuando registro el lote, fecha de vencimiento y costo de compra de cada uno, entonces las existencias aumentan, entran a la rotación vendiendo primero lo que vence antes (RN-19) y la solicitud pasa a Completada.
  2. Dado que intento ingresar para un producto una cantidad mayor a la aprobada, cuando confirmo, entonces el sistema advierte el exceso y bloquea la operación.
  3. Dado que ingreso un lote cuya fecha de vencimiento ya se cumplió o vence hoy, cuando intento confirmar, entonces el sistema bloquea la recepción conforme a la regla RN-03.
  4. Dado que registro el costo de compra en la recepción, cuando se confirma la entrada, entonces el sistema recalcula automáticamente el costo promedio ponderado de cada producto (RN-14).

---

### HU-SOL-05b · Reposición — Registrar una recepción parcial con saldo pendiente
- **Épica:** Mercadería y reposición
- **Historia:** Como encargado del almacén, quiero registrar una recepción parcial de mercadería dejando el saldo pendiente, para ingresar lo recibido y controlar lo que falta por entregar.
- **Reglas de negocio:** RN-01, RN-03, RN-14, RN-19
- **Criterios de aceptación:**
  1. Dado que recibo solo una parte de los artículos aprobados, cuando registro las unidades recibidas con lote, vencimiento vigente posterior a hoy (RN-03) y costo de compra, entonces las existencias aumentan, el costo promedio se actualiza (RN-14) y la solicitud pasa a «Parcialmente atendida».
  2. Dado que una solicitud está parcialmente atendida, cuando abro su detalle, entonces visualizo claramente las cantidades recibidas y el saldo pendiente de cada artículo.
  3. Dado que llega el saldo restante de mercadería, cuando registro la segunda entrega cumpliendo fechas vigentes, entonces el sistema suma las existencias restantes con rotación de vencimiento (RN-19), pasa la solicitud a Completada y deja el saldo pendiente en cero.

---

## 8.4 EPIC-VEN — Ventas y caja (18 HUs · 59 SP)

---

### HU-CAJA-01 · Abrir el turno de caja
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero abrir el turno de caja declarando el dinero en efectivo que tengo al comenzar, para disponer de sencillo para dar vuelto y habilitar las ventas en el mostrador.
- **Reglas de negocio:** RN-10, RN-29
- **Criterios de aceptación:**
  1. Dado que ingreso con rol `VENDEDOR` y no existe un turno abierto, cuando declaro un monto inicial válido en soles, igual o mayor que cero y con máximo dos decimales, entonces el sistema abre un turno ligado a mi usuario y habilita la preparación de ventas (RN-10, RN-29).
  2. Dado que ingreso un monto negativo, no numérico o con más de dos decimales, cuando intento confirmar, entonces el sistema explica la validación, no abre el turno y no registra movimiento de efectivo.
  3. Dado que ya existe un turno abierto o dos vendedores intentan abrirlo simultáneamente, cuando el sistema procesa las solicitudes, entonces exactamente una apertura como máximo queda confirmada y las demás se rechazan sin crear turnos paralelos (RN-10).
  4. Dado que la apertura se confirmó, cuando consulto el turno, entonces conserva vendedor responsable, caja única, dinero inicial e instante inequívoco mostrado con fecha y hora de Lima; un rol no autorizado no puede abrirlo por acceso directo (RN-29).

---

### HU-CAJA-02 · Cerrar y cuadrar la caja
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero cerrar mi turno de caja ingresando el dinero en efectivo contado, para generar el resumen de cuadre y comparar la plata contada contra el dinero esperado.
- **Reglas de negocio:** RN-10, RN-29, RN-30
- **Criterios de aceptación:**
  1. Dado que ingreso como el `VENDEDOR` responsable del turno, cuando declaro el efectivo contado, entonces el sistema exige un valor numérico igual o mayor que cero con máximo dos decimales; ante un valor inválido o un rol distinto no cierra ni modifica el turno (RN-10, RN-29).
  2. Dado que el monto contado es válido, cuando se prepara el resumen, entonces calcula `esperado = inicial + ingresos confirmados de efectivo - salidas confirmadas de efectivo` y `diferencia = contado - esperado`, mostrando cuadre exacto, sobrante o faltante; en Sprint 1 los ingresos posteriores a la apertura son los totales de ventas en efectivo confirmadas (RN-10).
  3. Dado que confirmo un cierre válido, cuando se guarda, entonces registra vendedor, caja, importes e instante de cierre mostrado en Lima y deja el turno cerrado de forma irreversible; un segundo intento de cierre se rechaza sin alterar el acta original (RN-10).
  4. Dado que existe una venta en preparación con al menos una línea, cuando intento cerrar, entonces el sistema bloquea el cierre hasta cobrarla, quitar su última línea o descartarla; si un cobro y el cierre compiten, solo uno se confirma primero y la venta queda incluida en el esperado o es rechazada por turno cerrado, nunca confirmada fuera del cuadre (RN-10, RN-30).
  5. Dado que el turno quedó cerrado, cuando se intenta vender con él, entonces el sistema rechaza la operación y permite que después se abra otro turno con nuevo dinero inicial, sin coexistencia de dos turnos abiertos (RN-10).

---

### HU-CAJA-03 · Caja — Registrar movimiento manual de efectivo
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero registrar ingresos o salidas manuales de efectivo en la caja durante mi turno, para justificar movimientos de dinero que no provienen de una venta.
- **Reglas de negocio:** RN-10, RN-11, RN-15
- **Criterios de aceptación:**
  1. Dado que registro un movimiento manual de efectivo, cuando indico el monto, entonces el sistema exige que sea mayor que cero y registrar obligatoriamente el motivo y el responsable de la operación (RN-11).
  2. Dado que registro el movimiento en dinero en efectivo, cuando confirmo, entonces el sistema guarda la fecha, hora exacta y monto, reflejándolo en el resumen del turno.
  3. Dado que los movimientos manuales son exclusivamente en efectivo, cuando intento seleccionar otra modalidad, entonces el sistema no lo permite (RN-15).
  4. Dado que existen ingresos o salidas manuales confirmadas, cuando se calcula el dinero esperado al cerrar la caja, entonces se consideran sumando los ingresos manuales y restando las salidas manuales.

---

### HU-CAJA-04 · Caja — Ver resumen del turno activo
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero consultar en cualquier momento el resumen de cobros y movimientos de mi turno en curso, para conocer el saldo estimado en gaveta.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que tengo un turno abierto, cuando abro el resumen, entonces veo el monto inicial, el total de ventas cobradas, los movimientos manuales y el saldo estimado en efectivo.
  2. Dado que se cobra una nueva venta o movimiento, cuando se actualiza la pantalla, entonces los totales reflejan el estado vigente sin necesidad de cerrar el turno.

---

### HU-CAJA-05 · Caja — Consultar historial de turnos de caja
- **Épica:** Ventas y caja
- **Historia:** Como administrador o dueño, quiero consultar el historial de turnos pasados con sus totales de ventas y cuadres, para revisar diferencias de dinero y desempeño.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al historial de turnos, cuando la lista carga, entonces veo por cada turno: vendedor, fechas y horas de apertura y cierre, dinero inicial, total cobrado, dinero declarado y diferencia.
  2. Dado que aplico filtros por vendedor o rango de fechas, cuando consulto, entonces la pantalla muestra los turnos correspondientes.

---

### HU-CAJA-06 · Caja — Aprobar cierre de turno
- **Épica:** Ventas y caja
- **Historia:** Como administrador o dueño, quiero revisar y validar formalmente el cuadre de un turno cerrado, para dejar constancia de la conformidad administrativa.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que un turno se encuentra en estado Cerrado, cuando el administrador lo revisa y aprueba, entonces pasa a estado Aprobado y queda bloqueado ante modificaciones.
  2. Dado que el turno registró sobrante o faltante, cuando el administrador lo aprueba, entonces el sistema guarda la observación con la diferencia detectada.

---

### HU-CAJA-07 · Caja – Forzar cierre de turno de caja
- **Épica:** Ventas y caja
- **Historia:** Como administrador, quiero forzar el cierre administrativo de un turno de caja abandonado tras 2 horas o más de inactividad, para liberar la caja y regularizar la operación.
- **Reglas de negocio:** RN-23
- **Criterios de aceptación:**
  1. Dado que un turno de caja no registra ventas ni movimientos durante 2 horas consecutivas o más (RN-23), cuando el administrador consulta la caja, entonces el sistema habilita la opción de Cierre Forzado Administrativo.
  2. Dado que el administrador confirma el cierre forzado, cuando el sistema lo procesa, entonces cierra el turno bajo la condición de cierre por inactividad, genera el resumen con las ventas acumuladas y libera la caja para una nueva apertura.

---

### HU-VEN-01a · Ventas — Bloquear la pantalla de venta por inactividad
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero que la pantalla de venta se bloquee tras 5 minutos de inactividad, para evitar que terceros operen la caja cuando me alejo del mostrador.
- **Reglas de negocio:** RN-22
- **Criterios de aceptación:**
  1. Dado que la pantalla de venta permanece sin uso durante 5 minutos continuos, cuando se cumple dicho tiempo, entonces se bloquea automáticamente protegiendo la caja (RN-22).
  2. Dado que la pantalla está bloqueada, cuando intento cualquier acción, entonces el sistema me exige reingresar mi contraseña.
  3. Dado que reingreso mi contraseña correcta, cuando el sistema la valida, entonces regreso a la pantalla de venta conservando la venta en curso sin pérdida de datos.

---

### HU-VEN-01b · Preparar una venta y revisar existencias
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero buscar productos, indicar cantidades y revisar las existencias disponibles antes de cobrar, para atender al cliente en mostrador con los precios y totales claros.
- **Reglas de negocio:** RN-03, RN-10, RN-27, RN-29, RN-30
- **Criterios de aceptación:**
  1. Dado que ingreso con rol `VENDEDOR`, cuando inicio la preparación y agrego la primera línea válida, entonces el sistema exige un turno abierto ligado a mi propio usuario y crea la venta en preparación; cualquier otro rol o vendedor sin ese turno recibe una denegación (RN-10, RN-29, RN-30).
  2. Dado que preparo la venta, cuando busco un producto enlatado activo por nombre o digitando su código de barras, entonces puedo seleccionarlo si posee existencias vendibles, sin requerir lector físico en Sprint 1.
  3. Dado que agrego o actualizo un producto, cuando indico la cantidad, entonces exige un entero mayor que cero, agrupa el mismo producto en una sola línea y rechaza un total superior a sus existencias vendibles.
  4. Dado que un lote vence hoy o ya venció según la fecha de `America/Lima`, cuando el sistema calcula las existencias vendibles, entonces excluye todas sus unidades y nunca las ofrece para completar la cantidad solicitada (RN-03).
  5. Dado que la lista contiene líneas, cuando reviso la venta, entonces se considera una venta en preparación que aún no reserva ni descuenta stock ni mueve efectivo; muestra precio unitario, cantidad, importe por línea, total y el desglose `base = HALF_UP(total / 1.18, 2)` e `IGV = total - base`. Si quito la última línea, el borrador se descarta y deja de bloquear el cierre; al descartarlo, caja y existencias quedan intactas (RN-27, RN-30).

---

### HU-VEN-01c · Cobrar en efectivo y descontar existencias
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero cobrar la venta en efectivo, calcular el vuelto y descontar la mercadería de los lotes adecuados, para completar la atención y mantener el inventario al día.
- **Reglas de negocio:** RN-03, RN-10, RN-19, RN-25, RN-27, RN-28, RN-29, RN-30
- **Criterios de aceptación:**
  1. Dado que una venta en preparación tiene líneas y el efectivo ingresado es no numérico, tiene más de dos decimales o resulta menor que el total, cuando intento cobrar, entonces el sistema rechaza la operación, informa el faltante cuando corresponda y no crea venta, correlativo o movimiento ni modifica existencias (RN-30).
  2. Dado que ingreso un efectivo válido igual o mayor al total, cuando confirmo, entonces el sistema calcula `vuelto = efectivo recibido - total` con dos decimales y aumenta el efectivo esperado solo por el total vendido, no por el efectivo recibido antes del vuelto (RN-10, RN-27).
  3. Dado que mi turno sigue abierto y existe stock suficiente al confirmar, cuando se descuentan unidades, entonces el sistema revalida las condiciones y aplica FEFO por vencimiento, instante de ingreso e identificador interno, continúa por los lotes vigentes necesarios y nunca deja existencias negativas (RN-03, RN-19, RN-29).
  4. Dado que el cobro se procesa, cuando la operación termina, entonces venta, detalles históricos, asignaciones de lotes, movimiento de efectivo, descuento de existencias y correlativo global `V-00000001` se confirman juntos; ante cualquier fallo no se confirma ninguna parte (RN-25).
  5. Dado que se produce doble clic, reenvío, reintento o competencia por las últimas unidades, cuando el sistema procesa las solicitudes, entonces un mismo intento lógico genera como máximo una venta, un movimiento, un correlativo y un descuento, y solo cobran las operaciones para las que existe stock confirmado (RN-25).
  6. Dado que la venta queda confirmada, cuando se guarda su fotografía histórica, entonces conserva nombre del producto, cantidad, precio con dos decimales, costo promedio con cuatro decimales, importes, efectivo y vuelto; cambios posteriores del catálogo o del costo no alteran esos valores (RN-28).

---

### HU-VEN-02a · Generar una constancia interna de venta
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero generar una constancia interna numerada de la venta cobrada, para entregar al cliente un respaldo de su compra y mantener el control interno del minimarket.
- **Reglas de negocio:** RN-26, RN-27, RN-29
- **Criterios de aceptación:**
  1. Dado que la venta fue confirmada con un correlativo global `V-00000001`, cuando se genera la constancia, entonces reutiliza exactamente ese número sin asignar otro y ofrece al vendedor verla en pantalla y abrir una vista preparada para la impresión del navegador (RN-26).
  2. Dado que reviso la constancia, cuando carga su contenido histórico, entonces muestra fecha y hora de Lima, vendedor, caja, nombre de cada producto, cantidad, precio e importe, base, IGV, total, efectivo y vuelto, pero nunca muestra el costo de compra o costo promedio (RN-26, RN-27).
  3. Dado que la constancia se visualiza o imprime, cuando se lee el documento, entonces exhibe de forma visible «CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO» e indica que la boleta o factura real se entrega por el canal autorizado habitual, sin logotipos ni leyendas que simulen aprobación de SUNAT (RN-26).
  4. Dado que el vendedor usa «Última constancia» desde la pantalla de venta de su turno, cuando la vuelve a abrir, entonces recupera el mismo correlativo y los mismos datos históricos aunque el catálogo cambie; un rol no autorizado no puede consultarla mediante acceso directo (RN-26, RN-29).

---

### HU-VEN-04 · Ventas – Buscar producto por código de barras
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero leer el código de barras de un producto en el mostrador para consultar de inmediato su precio y existencias, para responder rápido al cliente sin alterar la venta en curso.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que paso el código de barras de un producto por el lector en la consulta rápida, cuando el sistema lo reconoce, entonces muestra nombre, precio vigente y existencias vendibles sin agregarlo a la lista de venta.
  2. Dado que el código de barras leído no pertenece a ningún producto registrado, cuando se busca, entonces muestra «Producto no encontrado».

---

### HU-VEN-05a · Ventas — Consultar las ventas de mi turno
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero consultar las ventas confirmadas de mi turno activo, para verificar los cobros realizados y facilitar el cuadre antes de cerrar la caja.
- **Reglas de negocio:** RN-07
- **Criterios de aceptación:**
  1. Dado que tengo un turno de caja abierto, cuando consulto las ventas, entonces veo únicamente las operaciones confirmadas por mi usuario en el turno en curso (RN-07).
  2. Dado que reviso la lista de ventas del turno, cuando consulto los totales acumulados, entonces el total cobrado en efectivo y canales digitales coincide con los registros internos guardados.

---

### HU-VEN-05b · Ventas — Consultar el historial de ventas con filtros
- **Épica:** Ventas y caja
- **Historia:** Como administrador o dueño, quiero consultar el historial general de ventas confirmadas aplicando filtros por fecha, vendedor y turno, para supervisar las operaciones de la bodega.
- **Reglas de negocio:** RN-07
- **Criterios de aceptación:**
  1. Dado que ingreso como administrador o dueño, cuando abro el historial de ventas, entonces visualizo las ventas confirmadas registradas por todos los empleados (RN-07).
  2. Dado que aplico filtros por rango de fechas, vendedor o turno, cuando consulto, entonces la pantalla muestra únicamente las operaciones que cumplen los criterios.
  3. Dado que selecciono una venta de la lista, cuando abro su detalle completo, entonces veo productos, cantidades, precios, base imponible, IGV, total, medio de pago y constancia interna.

---

### HU-VEN-06a · Ventas — Anular una venta cobrada en efectivo
- **Épica:** Ventas y caja
- **Historia:** Como administrador o dueño, quiero anular una venta cobrada en efectivo de un turno abierto, para corregir errores de mostrador y devolver el dinero sin descuadrar la caja.
- **Reglas de negocio:** RN-08, RN-10
- **Criterios de aceptación:**
  1. Dado que la venta pertenece a un turno de caja abierto, cuando el administrador autoriza la anulación indicando el motivo justificado, entonces la venta pasa a estado Anulada y se emite la constancia interna de anulación.
  2. Dado que la venta fue cobrada en efectivo, cuando se confirma la anulación, entonces el sistema descuenta dicho monto del dinero esperado del turno activo.
  3. Dado que el turno de caja ya se encuentra cerrado o con cierre forzado, cuando intento anular una venta de ese turno, entonces el sistema bloquea la operación conforme a la regla RN-08.

---

### HU-VEN-06b · Ventas — Anular una venta cobrada con Yape
- **Épica:** Ventas y caja
- **Historia:** Como administrador o dueño, quiero anular una venta cobrada con billetera digital Yape registrando los datos de anulación, para respaldar el reintegro al cliente.
- **Reglas de negocio:** RN-08
- **Criterios de aceptación:**
  1. Dado que la venta fue cobrada con Yape en un turno abierto, cuando el administrador confirma la anulación, entonces el sistema registra la anulación capturando el código de autorización original y el motivo.
  2. Dado que se finaliza la anulación de una venta digital, cuando el sistema la procesa, entonces emite la constancia interna de anulación indicando que no afecta el efectivo físico en gaveta.

---

### HU-VEN-06c · Ventas — Definir el destino de la mercadería devuelta
- **Épica:** Ventas y caja
- **Historia:** Como encargado del almacén o administrador, quiero calificar los productos de una venta anulada para regresarlos al stock o enviarlos a merma, para mantener el inventario correcto.
- **Reglas de negocio:** RN-09
- **Criterios de aceptación:**
  1. Dado que los productos devueltos están en óptimas condiciones, cuando se confirma la anulación, entonces regresan a las existencias disponibles dentro de su lote original (RN-09).
  2. Dado que los productos devueltos presentan daños, abolladuras o están abiertos, cuando se procesa la anulación, entonces se derivan directamente a baja por merma (RN-09).
  3. Dado que se define el destino de la mercadería, cuando consulto los movimientos del producto, entonces visualizo el reingreso o la baja con su responsable.

---

### HU-VEN-07 · Cobrar con Yape y registrar el código de operación
- **Épica:** Ventas y caja
- **Historia:** Como vendedor, quiero registrar el cobro realizado con Yape ingresando el código de operación tras comprobar el ingreso del dinero en el teléfono de la bodega, para asentar la venta como pagada y entregar la constancia al cliente.
- **Reglas de negocio:** RN-02
- **Criterios de aceptación:**
  1. Dado que el cliente paga con Yape, cuando el vendedor revisa fuera del sistema en el teléfono o medio habitual de la bodega y declara haber comprobado que el dinero realmente llegó, entonces el sistema habilita el registro del cobro con Yape (RN-02).
  2. Dado que el vendedor intenta confirmar el cobro sin declarar que comprobó el ingreso del dinero en Yape, cuando pulsa el botón de confirmar, entonces el sistema no confirma la venta y solicita verificar primero el abono en el teléfono del minimarket.
  3. Dado que se procede al cobro con Yape, cuando el vendedor ingresa los datos, entonces el código de operación es obligatorio y debe escribirse completo tal como aparece en la operación de Yape, impidiendo guardar la venta si el campo queda vacío.
  4. Dado que se ingresa un código de operación que ya fue utilizado en una venta anterior, cuando se intenta confirmar el cobro, entonces el sistema advierte que el código ya fue registrado e impide utilizarlo nuevamente (RN-02).
  5. Dado que el vendedor declaró haber comprobado el ingreso y escribió un código de operación no utilizado previamente, cuando confirma la operación, entonces la venta queda registrada como pagada con Yape y se descuentan las existencias de mercadería.
  6. Dado que la venta con Yape queda registrada como pagada, cuando concluye la transacción, entonces la venta conserva el código de operación junto con el registro y genera su constancia interna de venta para el cliente y el control del negocio.

---

## 8.5 EPIC-REP — Control del negocio (16 HUs · 51 SP)

---

### HU-CONF-01 · Configuración — Ver configuración actual del negocio
- **Épica:** Control del negocio
- **Historia:** Como administrador o dueño, quiero ver los datos de la bodega configurados en el sistema (nombre comercial, RUC, dirección, teléfono y logotipo propio), para comprobar que la información sea correcta.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo a la sección de configuración, cuando la pantalla carga, entonces veo el nombre del minimarket, RUC, dirección, teléfono y logotipo propio que se usan en la constancia interna.
  2. Dado que faltan datos por registrar, cuando consulto la configuración, entonces el sistema señala con una advertencia visual los datos incompletos.

---

### HU-CONF-02 · Configuración — Actualizar configuración del negocio
- **Épica:** Control del negocio
- **Historia:** Como administrador, quiero actualizar el nombre del minimarket, RUC, dirección, teléfono y logotipo propio, para que las constancias internas reflejen la información vigente.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que actualizo el nombre comercial, RUC, dirección o teléfono y guardo, cuando se genera una nueva constancia interna de venta, entonces los datos actualizados aparecen en el encabezado.
  2. Dado que cargo una imagen con el logotipo propio de la bodega, cuando guardo, entonces el logo se muestra en la constancia interna y en la pantalla principal.
  3. Dado que el sistema emite únicamente constancias internas sin validez tributaria, cuando guardo la configuración, entonces no se definen series de facturas ni boletas oficiales.

---

### HU-DASH-01 · Resumen del negocio — Ver indicadores de ventas en tiempo real
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero ver en el resumen del negocio los indicadores comerciales del día (ventas totales, cantidad de operaciones y ticket promedio), para seguir el movimiento de la bodega en tiempo real.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que ingreso al resumen del negocio, cuando carga la pantalla, entonces muestra los indicadores del día: Ventas Totales en soles, Número de Ventas y Ticket Promedio.
  2. Dado que se cobra una nueva venta en mostrador, cuando se confirma la operación, entonces los indicadores del día se recalculan y muestran las cifras actualizadas.
  3. Dado que selecciono un período (Hoy, Esta semana, Este mes), cuando aplico la opción, entonces los indicadores presentan las cifras correspondientes al rango.

---

### HU-DASH-02 · Resumen del negocio — Ver gráfico de evolución de ventas por día
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero ver un gráfico con la evolución diaria de ventas en el período seleccionado, para evaluar las altas y bajas en las ventas del minimarket.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al resumen del negocio y existen ventas en el período, cuando el gráfico carga, entonces muestra el monto vendido por cada día del lapso elegido.
  2. Dado que en un día determinado no hubo ventas, cuando se grafica, entonces dicho día se representa con valor cero sin errores.

---

### HU-DASH-03 · Resumen del negocio – Ver alertas operativas (stock crítico, vencimientos y turnos)
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero ver en el resumen del negocio las alertas de productos con existencias mínimas, lotes por vencer y turnos sin actividad, para tomar decisiones oportunas.
- **Reglas de negocio:** RN-06, RN-23
- **Criterios de aceptación:**
  1. Dado que uno o más productos se encuentran en o por debajo de su cantidad mínima (10 unidades por defecto según RN-06), cuando abro el resumen, entonces muestra la alerta de existencias críticas indicando el producto y las unidades disponibles.
  2. Dado que existen lotes de mercadería cuya caducidad se cumplirá en los próximos 7 días, cuando consulto las alertas, entonces el sistema advierte el vencimiento inminente con el lote y los días restantes.
  3. Dado que un turno de caja permanece abierto sin operaciones durante 2 horas consecutivas o más (RN-23), cuando el sistema revisa los turnos, entonces muestra la alerta informativa de turno inactivo u olvidado.

---

### HU-DASH-04 · Resumen del negocio – Ver ranking de productos más vendidos
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero ver en el resumen del negocio un recuadro informativo con los 5 productos más vendidos del período, para reconocer los artículos con mayor rotación en mostrador.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al resumen del negocio, cuando carga el recuadro informativo, entonces muestra los 5 productos con mayor cantidad de unidades vendidas en el período.
  2. Dado que no existen ventas registradas en dicho período, cuando carga el recuadro, entonces informa «Sin ventas registradas en este período».

---

### HU-DASH-05 · Resumen del negocio — Ver solicitudes de reposición pendientes
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero ver en el resumen del negocio la lista de solicitudes de reposición pendientes de revisión, para atender las compras sin demoras.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que existen solicitudes en estado Pendiente, cuando abro el resumen, entonces el recuadro muestra el producto sugerido, la cantidad, el empleado solicitante y la fecha.
  2. Dado que selecciono una solicitud en el recuadro, cuando hago clic, entonces me conduce a la pantalla para aprobar o rechazar dicha solicitud.
  3. Dado que no existen solicitudes pendientes, cuando abro la pantalla, entonces informa «Sin solicitudes pendientes».

---

### HU-REP-01 · Reportes — Consultar reporte analítico de ventas totales por período
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero consultar un reporte detallado de ventas con filtros por fecha y medio de pago, para analizar los ingresos de la bodega.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que ingreso al reporte analítico de ventas, cuando selecciono un rango de fechas, entonces el sistema lista las ventas con fecha, número interno, medio de pago, base imponible, IGV y total.
  2. Dado que aplico el filtro por medio de pago (efectivo o Yape digital), cuando consulto, entonces muestra únicamente las operaciones cobradas por dicho canal y su suma acumulada.

---

### HU-REP-02 · Reportes – Consultar reporte completo de ranking de productos más vendidos
- **Épica:** Control del negocio
- **Historia:** Como dueño de la bodega, quiero consultar el ranking completo de productos vendidos y su porcentaje de participación, para identificar los artículos más demandados y planificar compras.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que consulto el reporte de ranking en un rango de fechas, cuando se generan los resultados, entonces ordena los productos de mayor a menor según las unidades vendidas y el importe total cobrado.
  2. Dado que se calcula la participación sobre las ventas del período, cuando reviso cada fila, entonces muestra el porcentaje de participación de cada producto sobre el total vendido.
  3. Dado que deseo ordenar la tabla, cuando hago clic en los encabezados, entonces permite ordenar por unidades vendidas o por monto total.

---

### HU-REP-03 · Reportes — Ver ventas desglosadas por día
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero consultar las ventas detalladas día por día dentro de un período, para conocer los días de mayor movimiento en la tienda.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al reporte de ventas por día, cuando el informe carga, entonces veo una fila por cada día del período con el total de dinero vendido y la cantidad de operaciones.
  2. Dado que un día del rango no registró ventas, cuando aparece en el reporte, entonces muestra cero sin omitir el día de la lista.

---

### HU-REP-04 · Reportes — Ver ventas por método de pago
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero consultar el desglose de ventas según el medio de cobro (efectivo o digital), para conciliar los ingresos y vigilar el efectivo disponible.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al reporte de medios de pago, cuando carga el informe, entonces veo el total recaudado en efectivo y el total recaudado por Yape en el período.
  2. Dado que aplico un filtro de fechas, cuando el informe se actualiza, entonces los montos reflejan exclusivamente las ventas del rango elegido.

---

### HU-REP-05 · Reportes – Consultar reporte de productos bajo stock mínimo
- **Épica:** Control del negocio
- **Historia:** Como administrador o dueño, quiero consultar un reporte de los productos que están en o por debajo de su cantidad mínima configurada, para coordinar los pedidos de mercadería a tiempo.
- **Reglas de negocio:** RN-06
- **Criterios de aceptación:**
  1. Dado que accedo al reporte de existencias críticas, cuando el sistema lo genera, entonces lista todos los artículos cuyo stock disponible actual es menor o igual al umbral mínimo configurado (10 unidades por defecto según RN-06).
  2. Dado que visualizo la lista, cuando consulto cada artículo, entonces muestra existencias actuales, cantidad mínima, categoría y unidad de medida.
  3. Dado que un producto tiene existencias en cero, cuando aparece en la lista, entonces se resalta con el estado «Agotado» para priorizar su reposición.

---

### HU-REP-06 · Reportes — Ver resumen general del inventario
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero consultar el resumen de existencias de todos los productos, para tener visibilidad completa del almacén sin realizar un conteo físico completo.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que abro el resumen de existencias, cuando el informe carga, entonces veo todos los productos con su stock actual, cantidad mínima y una indicación de estado normal o crítico.
  2. Dado que busco un producto por nombre, cuando el sistema filtra, entonces muestra solo los productos coincidentes.

---

### HU-REP-07 · Reportes — Ver margen de ganancia por producto
- **Épica:** Control del negocio
- **Historia:** Como dueño de la bodega, quiero consultar el margen de ganancia de cada producto comparando su precio de venta contra el costo conservado al momento de cada venta, para evaluar la rentabilidad real de la mercadería.
- **Reglas de negocio:** RN-14, RN-27, RN-28
- **Criterios de aceptación:**
  1. Dado que accedo al reporte de rentabilidad, cuando el sistema lo genera, entonces presenta para cada producto su precio de venta neto sin IGV (RN-27), el costo promedio que tenía el producto al momento de cada venta guardado históricamente (RN-28) y la ganancia unitaria en soles.
  2. Dado que se calcula el margen comercial, cuando se despliega la tabla, entonces muestra el porcentaje de margen bruto obtenido sobre las ventas.
  3. Dado que filtro por categoría o rango de fechas, cuando consulto, entonces el sistema lista los productos vendidos en ese lapso evaluando el margen porcentual y la ganancia total obtenida.

---

### HU-REP-08 · Reportes — Ver mermas agrupadas por motivo
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero consultar el informe de bajas de mercadería agrupadas por motivo, para cuantificar las pérdidas y tomar acciones preventivas.
- **Reglas de negocio:** —
- **Criterios de aceptación:**
  1. Dado que accedo al reporte de mermas, cuando el informe carga, entonces veo las unidades dadas de baja agrupadas por causa reconocida (Vencimiento, Daño o rotura, y Robo o faltante) en el período seleccionado.
  2. Dado que aplico un filtro de fechas, cuando el informe se actualiza, entonces presenta únicamente las bajas registradas en ese rango.

---

### HU-REP-09 · Reportes — Exportar reportes analíticos de gestión a PDF
- **Épica:** Control del negocio
- **Historia:** Como dueño o administrador, quiero descargar en archivo PDF los reportes analíticos de gestión, para compartir información con el contador o archivarla físicamente.
- **Reglas de negocio:** —
- **Notas funcionales:** Función compartida para descargar reportes analíticos de gestión (ventas, ranking, existencias críticas, rentabilidad y mermas).
- **Criterios de aceptación:**
  1. Dado que visualizo un reporte analítico de gestión en pantalla, cuando elijo la opción de exportar a PDF, entonces el sistema genera y descarga un archivo PDF con los datos y filtros consultados.
  2. Dado que el reporte no contiene información en el período seleccionado, cuando intento descargarlo, entonces el archivo PDF se genera indicando que no hay datos registrados sin provocar errores.

---

## 8.6 Ideas fuera del horizonte académico

Estas ocho ideas no forman parte de las historias activas de la bodega y no tienen criterios de aceptación detallados ni puntaje asignado. Se registran para dejar constancia de las decisiones tomadas:

| ID | Nombre de la idea | Motivo de exclusión |
|---|---|---|
| `HU-CLI-01` | Clientes — Listar clientes registrados | Excede la venta directa en mostrador a público general de la bodega. |
| `HU-CLI-02` | Clientes — Captura y reconocimiento de clientes en ventas nominales | La identificación fiscal con DNI o RUC corresponde a la facturación electrónica futura fuera del alcance académico. |
| `HU-CLI-03` | Clientes — Editar correo electrónico de cliente | Vinculado a la gestión de clientes nominales, función fuera de alcance. |
| `HU-VEN-02b` | Ventas — Emitir boleta nominal de más de S/ 700.00 | Los comprobantes de pago autorizados con valor tributario se emiten por el canal externo habitual de la bodega. |
| `HU-VEN-02c` | Ventas — Emitir factura comercial con RUC | La facturación electrónica con RUC se gestiona por el canal autorizado externo. |
| `HU-VEN-03` | Ventas – Generar comprobante en PDF o reenviar por correo | El despacho digital de comprobantes fiscales queda supeditado a la facturación tributaria futura fuera de alcance. |
| `HU-VEN-08` | Ventas — Exportar historial de ventas a PDF | Las consultas de ventas se realizan directamente en pantalla; los reportes analíticos de gestión ya permiten su exportación. |
| `HU-VEN-09` | Ventas — Registrar venta a granel o por peso | La bodega comercializa exclusivamente productos envasados por unidad con código de barras. |

---

*Siguiente documento: Product Backlog priorizado (`09_Product_Backlog.md`).*


---

## 8.7 Trazabilidad de Criterios de Aceptación Endurecidos tras Auditoría QA/UX (`BUG-001` a `BUG-037`)

Para mantener trazabilidad estricta entre el Product Backlog, las Historias de Usuario implementadas en los Sprints 1–3 y las correcciones derivadas de la Auditoría de Caos Multi-Rol y UX (`REPORTE_CAOS_Y_UX_QA.md`), se documentan los criterios de aceptación verificados y endurecidos en código y pruebas unitarias (202 pruebas automatizadas en verde):

| Historia de Usuario | Criterio de Aceptación / Regla Endurecida | Hallazgo Cerrado | Prueba Unitaria Asociada |
|---|---|---|---|
| `HU-USR-01` / `HU-USR-03` · Listar y editar datos y rol de un empleado | **CA-4 (Protección de roles del minimarket):** Dado que un vendedor tiene un turno de caja en estado `OPEN`, cuando el Administrador intenta cambiar su rol a otro perfil (ej. `ALMACENERO`), entonces el sistema rechaza el cambio de rol e informa que debe cerrar el turno primero. Asimismo, impide degradar al único Administrador activo. | `BUG-001`, `BUG-021` | `identity.tests.EmployeeEditDeactivateTests.test_cannot_change_role_of_seller_with_open_shift` |
| `HU-CAJA-01` / `HU-CAJA-05` · Apertura e Historial de turnos de caja | **CA-3 (Visibilidad de diferencia de cuadre y cajero con turno abierto):** Dado que un turno ha sido cerrado, cuando el Administrador o Vendedor consulta `/caja/turnos/`, visualiza el importe exacto de la diferencia (`S/ -5,00`, `S/ 10,00`, `S/ 0,00`) y su clasificación (`Faltante`, `Sobrante`, `Exacto`). Si otro vendedor intenta abrir `/caja/abrir/` cuando ya existe turno activo, el sistema le informa el nombre del vendedor titular y la hora de apertura; y al abrir turno en `/caja/turnos/<id>/abierto/` ofrece enlace directo a preparar venta (`/ventas/`). | `BUG-002`, `BUG-022`, `BUG-023`, `BUG-031` | `cash.tests.CashShiftHistoryTests.test_shift_history_renders_shortage_surplus_and_exact_labels_and_amounts`, `test_bug023_and_bug031_cash_open_shows_owner_and_shift_opened_has_sales_draft_link` |
| `HU-INV-02` / `HU-INV-03` · Mermas y Ajustes físicos | **CA-5 (Idempotencia transaccional, `@never_cache`, prioridad de `POST lot_id` y recálculo de costo promedio):** Si un intento de baja o ajuste falla por validación, la clave de idempotencia no se consume prematuramente; las vistas usan `@never_cache` para evitar claves cacheadas al volver atrás; en `POST` se prioriza `request.POST["lot_id"]` sobre `?lote=` y se muestran errores de campos ocultos (`idempotency_key`, `lot_id`); y al registrar bajas o ajustes físicos se recalcula `product.average_cost`. | `BUG-003`, `BUG-005`, `BUG-010`, `BUG-036` | `inventory.tests.PhysicalAdjustmentTests.test_failed_validation_does_not_consume_idempotency_key_in_writeoff_or_adjustment`, `test_missing_idempotency_key_still_prevents_rapid_duplicate_adjustment`, `test_bug036_writeoff_and_adjustment_prioritize_posted_lot_id_and_render_hidden_field_errors`, `test_bug005_writeoff_and_physical_adjustment_recalculate_average_cost` |
| `HU-PROD-04` / `HU-INV-06` · Editar producto y Kardex | **CA-4 (Trazabilidad histórica en Kardex con FK directa e inmutabilidad de snapshot):** Cada `SaleLine` persiste la referencia `product` además del snapshot comercial, de modo que aunque el Administrador cambie el código de barras en `/productos/<id>/editar/`, las ventas históricas permanecen vinculadas en el Kardex y `product_snapshot_barcode` permanece inmutable en las constancias emitidas (`RN-28`). | `BUG-004`, `BUG-012` | `inventory.tests.PhysicalAdjustmentTests.test_barcode_change_preserves_sales_in_product_movements_kardex`, `catalog.tests.ProductExpirationsTests.test_bug004_product_barcode_update_preserves_historical_sale_line_snapshot`, `test_initial_load_created_preserves_original_quantity_and_alias_url` |
| `HU-INV-01a` / `HU-INV-01b` / `HU-PROV-01..04` · Cargas iniciales, Entradas posteriores y Proveedores | **CA-1..5 (Autoría por lote `Lot.responsible`, proveedor en carga inicial y acceso de Admin a constancia):** Cada lote persiste su almacenero responsable (`Lot.responsible`, migración `0005_lot_responsible`) y su proveedor (`Lot.supplier`). La constancia `/inventario/cargas/<id>/` es accesible tanto para `ALMACENERO` como para `ADMIN` (con enlace `"Ver carga"` en `/inventario/stock/`), preserva intactos los lotes iniciales y muestra el responsable real de cada entrada posterior; el Kardex muestra el proveedor tanto en carga inicial como en entradas posteriores y atribuye cada lote al almacenero que lo registró. | `BUG-005`, `BUG-011`, `BUG-014`, `BUG-024`, `BUG-027`, `BUG-030`, `BUG-032` | `inventory.tests.PhysicalAdjustmentTests.test_stock_entry_view_registers_subsequent_lots_and_links_supplier`, `test_bug024_stock_entry_preserves_initial_load_lots_and_labels_subsequent_entries_in_kardex`, `test_bug032_subsequent_stock_entry_records_second_warehouse_worker_and_admin_can_view_load`, `test_bug005_register_stock_entry_excludes_expired_lots_from_average_cost`, `test_bug027_lot_unit_cost_rejects_scientific_notation_and_excessive_values`, `catalog.tests.ProductExpirationsTests.test_bug030_seed_demo_populates_weighted_average_cost` |
| `HU-VEN-01b..01c` / descuento sin HU asignada · Borrador, Cobro en efectivo y Descuentos | **CA-6 (Sincronización ante cambio de precio/disponibilidad, firma con `draft.pk` y errores de campos ocultos):** Si el producto o su categoría se desactiva mientras está en el borrador, `update_draft_line` y `checkout_sale` rechazan incrementar la cantidad o cobrar. En `/ventas/cobrar/`, `_draft_signature` incluye `draft.pk`, nombre y código de barras de cada línea para impedir que una pestaña antigua cobre el borrador de un nuevo cliente (`BUG-035`), y renderiza errores de campos ocultos en `.alert-error` (`BUG-036`). | `BUG-006`, `BUG-007`, `BUG-025`, `BUG-029`, `BUG-033`, `BUG-035`, `BUG-036`, `BUG-037` | `sales.tests.SalesHistoryTests.test_price_change_during_checkout_warns_seller_and_updates_draft_line_price`, `test_multitab_draft_modification_warns_seller_on_checkout`, `test_bug025_checkout_detects_same_subtotal_product_swap_via_draft_signature`, `test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout`, `test_bug035_and_bug036_draft_signature_includes_draft_id_and_checkout_renders_hidden_field_errors` |
| `HU-VEN-02a` / `HU-VEN-05a..05b` · Constancia e Historial de ventas | **CA-4 (Navegación por rol y visibilidad de descuentos):** Dado que el Administrador consulta una constancia en `/ventas/constancia/<id>/`, ve el botón `Volver al historial` y no ve enlaces exclusivos de Vendedor (`Nueva venta`). En `/ventas/historial/` y `/ventas/historial/turno/` se exhibe la columna `Descuento (S/)` y los totales acumulados. | `BUG-008`, `BUG-015`, `BUG-023` | `sales.tests.SalesHistoryTests.test_sales_receipt_hides_nueva_venta_for_admin_and_shows_back_to_history`, `test_sales_history_and_shift_history_display_discount_column_and_totals` |
| `HU-CAT-01..02` / `HU-PROD-01..04` · Categorías y Catálogo de productos | **CA-2 (Ciclo de vida coherente de categorías activas e inactivas):** Toda categoría activa puede usarse al registrar o editar productos y activarse/desactivarse en `/productos/categorias/`. Si una categoría se desactiva, sus productos siguen permitiendo editar precio/nombre/stock mínimo en `/productos/<id>/editar/` manteniendo su categoría actual, pero quedan excluidos de los selectores de carga inicial y entrada de mercadería (`InitialLoadProductForm`, `StockEntryProductForm`) y de la venta en mostrador (`_search_products`, `add_product_to_draft`, `update_draft_line`, `checkout_sale`). | `BUG-009`, `BUG-013`, `BUG-021`, `BUG-028`, `BUG-031`, `BUG-033` | `catalog.tests.ProductExpirationsTests.test_active_custom_category_can_be_used_to_register_product`, `test_bug028_category_toggle_and_product_edit_category_and_barcode_search`, `test_bug033_product_with_inactive_category_can_update_price_and_name`, `inventory.tests.PhysicalAdjustmentTests.test_bug033_inactive_category_excludes_products_from_initial_load_and_stock_entry_forms` |
| `HU-AUTH-01` / `HU-AUTH-03` / `HU-INV-05` · Login, Inicio, Cierre de sesión y Diseño UI | **CA-3 (registro histórico de alertas y coherencia visual):** La descripción histórica del bloqueo de cinco minutos quedó reemplazada: el ingreso principal bloquea el identificador durante 15 minutos tras cinco fallos y comparte el bloqueo entre sesiones (véase HU-AUTH-02 y la guía de alcance actual). `/inicio/` muestra el conteo de lotes vencidos a Admin y Almacenero con un único `<h1>`; `/salir/`, `403.html` y `404.html` muestran la marca correspondiente al rol del usuario; y `app.css` unifica el diseño visual. | `BUG-016`..`BUG-020`, `BUG-023`, `BUG-026`, `BUG-031` | `identity.tests.EmployeeEditDeactivateTests.test_login_lock_expires_after_fifteen_minutes`, `test_dashboard_for_admin_and_warehouse_includes_expired_lots_and_single_h1`, `test_logout_confirm_shows_minimarket_title_and_draft_warning_for_seller`, `test_employee_list_does_not_render_broken_bootstrap_dismiss_button` |

## Registro de revisión de catálogo · 09/11/2026

- **DOC03-01, decisión aceptada del usuario:** «Productos de cualquier categoría, por unidad y con vencimiento obligatorio». HU-PROD-02 pasa de «Registrar un producto enlatado» y CA01 ligado a «Productos enlatados» preparada en R1 a cualquier categoría activa, UND y vencimiento obligatorio. El requisito original y su evaluación como conflicto se conservan en los inventarios/evidencias03-A aE; esta revisión no convierte aquellos resultados históricos en aprobados.
- **DOC-00-14, conciliación con el pedido del usuario:** HU-PROD-01 decía «Como administrador o vendedor»; ahora ADMIN/ALMACENERO consultan catálogo y el vendedor utiliza la consulta de su flujo de venta autorizado. Se mantiene RN29 y no se amplían rutas ni permisos.
- No cambian CA02–05 de HU-PROD-02, el conflicto de código editable en HU-PROD-04 ni el estado futuro de CAT03/04 y PROD03. [Informe de revisión y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md).

- **DOC03-02, decisión aceptada del usuario:** «Sí, podrá corregirlo si es único y conserva los históricos». HU-PROD-04/CA03 deja de exigir campo bloqueado; exige corrección ADMIN, unicidad normalizada, identidad/referencias y snapshots históricos conservados. La redacción previa y conflicto de03-A aF se conservan en sus evidencias. No autoriza reasignar automáticamente historias ambiguas de códigos reutilizados.
- **HU-PROD-03, tecnología indicada:** Barcode to PC Server. La propuesta inicial definió el medio de captura. El 10/11/2026 se verificó CA01 en alta mediante el diálogo «Escanear código», usando dos etiquetas físicas. La aplicación también permite corregir un código en edición y rechaza un duplicado al guardar. CA02, aviso inmediato al leer, sigue previsto. Se conserva la selección histórica de la HU. [Propuesta inicial](auditoria_por_etapas/resultados/anexos/ETAPA-03-G-codigo-y-lector.md) · [Evidencia física de 03-K9](auditoria_por_etapas/resultados/evidencias/03-K-phone-20261111T011843801709Z/phone.json).


## Decisiones de stock mínimo y nombres · 10/11/2026

El usuario aceptó con «bien, continua» las recomendaciones inmediatamente anteriores: máximo técnico999999 con predeterminado10 al registrar, y nombres únicos ignorando mayúsculas/espacios redundantes, distinguiendo marca/contenido/presentación. Se aceptan PROP-03C-LIMITES y PROP-03C-NOMBRE; no son nuevas HU. Regla de nombre común a PROD02-CA01 y PROD04-CA04: unicidad global, incluso inactivos y otras categorías; la propia ficha puede conservar su nombre. Se mantiene la equivalencia Unicode NFC/casefold ya usada en búsqueda; no se eliminan acentos. Las ventas históricas conservan su texto.

Trazabilidad histórica: PROD02-CA04 decía «entero igual o mayor que cero», sin máximo; PROD04-CA04 solo exigía actualizar nombre en catálogo y pantalla de venta. La unicidad del nombre estaba limitada a formularios y podía eludirse con dos formularios ya validados. Las reglas aceptadas se verifican también en servicio y restricciones persistentes. Datos incompatibles previos requieren resolución explícita antes de migrar, sin fusionar ni recortar automáticamente. [Evidencia03-I](auditoria_por_etapas/resultados/anexos/ETAPA-03-I-politicas.md).


## Cambio de estado de una categoría · decisión del 10/11/2026

Se acepta el siguiente alcance de PROP-E00-HU-02, vinculada al agregado de ciclo de vida de categorías (08, fila QA de HU-CAT-01..02 / HU-PROD-01..04). Como administrador, quiero revisar el efecto de activar o desactivar una categoría antes de confirmarlo para evitar interrumpir por error las operaciones del almacén y las ventas en preparación.

| Criterio suplementario | Dado / cuando / entonces |
|---|---|
| J-CA1. Revisión y cancelación | Dada una categoría existente, cuando ADMIN elige Activar o Desactivar, ve nombre, estado actual, acción y efecto en productos, ventas en preparación e inventario. Abrir, recargar o cancelar conserva el estado. |
| J-CA2. Aplicación y conservación | Dada una revisión vigente, cuando ADMIN confirma, se aplica el destino solicitado. La suspensión bloquea la oferta y las operaciones correspondientes. La reactivación respeta el estado individual y las existencias vigentes. Se conservan lotes, borradores y ventas confirmadas. |
| J-CA3. Pantalla antigua | Dada una lista o confirmación abierta, cuando otro administrador cambia el estado, el siguiente intento desde la versión antigua informa del cambio y pide revisar el estado actual. Incluso si volvió al estado inicial, el envío antiguo se rechaza. |
| J-CA4. Acceso | Dada una cuenta distinta de ADMIN, al intentar revisar o confirmar recibe la respuesta prevista para su rol y el estado se conserva. |

Son criterios adicionales a los 27 CA base del tramo. CAT03 (renombrar), CAT04 (eliminar) y PROD03 (lector) mantienen su clasificación futura.

[Auditoría 03-J](auditoria_por_etapas/resultados/anexos/ETAPA-03-J-estado-categoria.md).


**Adenda03-O,10/11/2026 — HU-PROD-03 seleccionado:** pedido del usuario de aplicar mejoras pendientes. CA02 conserva el texto original y se implementa en el diálogo y campo manual: mensaje de duplicado antes del guardado; mismo criterio de unicidad para activos/inactivos, excluyendo ficha propia en edición. La consulta anticipada no reserva el código y el servidor revalida al guardar. Ante fallo de red se informa que no pudo comprobarse. La captura conserva revisión/copia expresa aceptada enK8/K9, sin guardado por Enter. CA01 evidencia físicaK9; CA02 evidencia softwareO, prueba física del aviso pendiente. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-N-O-reclasificacion-y-duplicados.md).

**Vigencia 03-P/W, 10/11/2026:** el aviso de PROD03/CA02 se verificó físicamente en P. El flujo vigente de CA01 llena el campo temporal al leer y exige «Usar código» para copiar a la ficha; la adenda03-O documenta la copia expresa aceptada. La redacción original08:231 aún dice llenado automático del campo y queda como discrepancia de redacción para aclarar, sin borrar el texto histórico. [Evidencia y conciliación](auditoria_por_etapas/resultados/anexos/ETAPA-03-W-conciliacion.md).

**Actualización03-X,11/11/2026 (ejecución10/11):** PROD03/CA02 queda PARCIAL en la frontera EAN13/UPC12: seis lecturas físicas recibieron12 dígitos ante una ficha almacenada con13 y el aviso no indicó duplicado. La unicidad literal conserva sus muestras favorables.69/69 controles navegador/HTTP/ORM,16/16 servicio/DB y9/9 observación física; estos últimos acreditan la observación, no la equivalencia. DEC-03X-IDENTIDAD y PROP-03X-CA01..03/T01..03 son propuestas pendientes, sin cambio funcional, fusión ni migración. No se modifican estimaciones/sprints históricos ni se aprueban otras etapas. [Evidencia, alternativas y criterios](auditoria_por_etapas/resultados/anexos/ETAPA-03-X-codigos-ean-upc.md).

**Actualización 03-Y · 11/11/2026.** PROD02–04. En alta, ADMIN elige GTIN o interno. Un GTIN unitario admitido reserva todas sus representaciones equivalentes. Un interno conserva sus ceros significativos. El aviso bloquea la copia si otra ficha reserva la lectura. Una corrección conserva la identidad y los históricos. [Evidencia 03-Y](auditoria_por_etapas/resultados/anexos/ETAPA-03-Y-identidad.md).

**Precisión 03-Z · 11/11/2026.** Se alineó CA01 de HU-PROD-03 con la revisión y copia expresa aceptadas en la adenda 03-O. La redacción anterior fue «Dado que tengo abierto el formulario de nuevo producto, cuando paso el código de barras por el lector, entonces el campo de código se llena automáticamente con el valor leído.». [Pruebas y trazabilidad](auditoria_por_etapas/resultados/anexos/ETAPA-03-Z-relectura-interna.md).


## Conciliación de carga inicial · 11/11/2026

DOC03-01 ya aceptado se aplica a la descripción de HU-INV-01a: el texto «producto enlatado» se sustituye por cualquier categoría activa, por unidad y con vencimiento obligatorio. La restricción anterior permanece en las evidencias históricas; se conservan sus cinco criterios y RN-01 para entradas posteriores. Esta corrección documental no selecciona recepción multiproducto en una sola transacción ni retiro sanitario. [Matriz y evidencia 05-E](auditoria_por_etapas/resultados/anexos/ETAPA-03-AF-conciliacion-carga.md).
