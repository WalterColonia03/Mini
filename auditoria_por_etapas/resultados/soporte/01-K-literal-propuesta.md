# 01-K · Ficha literal de presentación de ingreso

Ficha incorporada a08 bajo los criterios y casos existentes de HU-AUTH-01/02 por instrucción expresa de alinear la demostración. La fuente vigente es08; esta ficha conserva el refinamiento de presentación, sin funciones nuevas. Resultado:79/79 comprobaciones de literales en Chrome y4 pruebas de formulario; ver ETAPA-01, sublote01-K.

## Presentación vinculada a HU-AUTH-01/CA-01 y CP-HU-AUTH-01-001

En `GET /`, para visitante, el documento usa título «Ingresar — Sistema de gestión». La pantalla muestra los siguientes literales. Los elementos que actúan como navegación conservan el destino indicado; los textos de presentación no son botones ni conceden permisos.

| Elemento | Texto exacto / acción | Criterio relacionado |
|---|---|---|
| Marca superior y pie | «Minimarket», «Sistema de gestión», separados visualmente por marca o punto medio | CA-01, identidad del sistema |
| Enlace de marca | Vuelve al ingreso `/`; nombre accesible «Minimarket, inicio» | CA-01 |
| Enlace de salto | «Saltar al contenido»; lleva al contenido principal `#contenido` con teclado | CA-01, presentación accesible |
| Encabezado introductorio | «Gestión de minimarket» | CA-01 |
| Título principal | «Bienvenido. Escribe tu correo y tu contraseña.» | CA-01 |
| Explicación de roles | «Cada persona ve solo las operaciones de su puesto: administración, almacén y caja.» | CA-01, CA-04 y RN-29 |
| Tarjeta Administrador | «Administrador»; «Productos, empleados, proveedores y resumen diario de ventas.» | CA-01 y RN-29; destinos HU-PROD, HU-USR, HU-PROV y HU-DASH existentes |
| Tarjeta Almacenero | «Almacenero»; «Inventario, mermas y alertas de stock.» | CA-01 y RN-29; destinos HU-INV y consultas existentes |
| Tarjeta Vendedor | «Vendedor»; «Turno de caja y ventas.» | CA-01 y RN-29; destinos HU-CAJA/HU-VEN existentes |
| Etiqueta del formulario | «Acceso seguro» | CA-01, CA-02/03 y AUTH-02; no expresa garantía absoluta |
| Título del formulario | «Iniciar sesión» | CA-01 |
| Ayuda | «Usa tu cuenta de trabajo para continuar.» | CA-01 |
| Campo correo | Etiqueta «Correo de trabajo»; placeholder «nombre@empresa.com»; valor inicial vacío | CA-01 |
| Campo contraseña | Etiqueta «Contraseña»; placeholder «Ingrese su contraseña»; valor inicial vacío y entrada enmascarada | CA-01 |
| Botón de envío | «Iniciar sesión»; envía el formulario por POST | CA-01/02/03, AUTH-02 |
| Nota de permisos | «Tus permisos y acciones dependen del rol asignado.» | CA-04 y RN-29 |

Las letras «A», «B», «V» y el punto decorativo junto a la nota son iconos no interactivos, no acciones ni roles adicionales. Las tarjetas explican los tres roles y no permiten seleccionar uno para iniciar sesión. El rol procede de la cuenta autenticada. No se ofrece registro público, recuperación de contraseña, selección multirrol ni portal administrativo técnico.

El correo es obligatorio, admite hasta 254 caracteres después de quitar espacios exteriores y debe tener formato de correo. La autenticación normaliza con `strip().casefold()`; no se modifica la política IDNA. La contraseña es obligatoria, conserva sus espacios significativos y no se repuebla al mostrar errores. Los atributos de autocompletado son `username` y `current-password`; el correo recibe foco inicial. El tamaño de contraseña no recibe un máximo nuevo en esta ficha.

## Validación vinculada a HU-AUTH-01/CA-01/02/03 y CP-HU-AUTH-01-002

| Estado | Literal exacto esperado | Efecto |
|---|---|---|
| Correo vacío | «Este campo es obligatorio.» bajo el correo | No autentica ni cuenta un fallo de contraseña |
| Contraseña vacía | «Este campo es obligatorio.» bajo la contraseña | No autentica ni cuenta un fallo de contraseña |
| Formato de correo inválido | «Introduzca una dirección de correo electrónico válida.» | No autentica ni crea/incrementa intentos |
| Correo con N caracteres, N > 254 después de recortar extremos | «Asegúrese de que este valor tenga como máximo 254 caracteres (tiene {N}).» | No autentica ni crea/incrementa intentos |
| Carácter nulo en correo o contraseña, mediante POST alterado | «Los caracteres nulos no están permitidos.»; en correo aparece además el mensaje de formato inválido | No autentica ni crea/incrementa intentos |
| Contraseña equivocada de cuenta existente | «Correo o contraseña incorrectos» | Deniega y cuenta el fallo según RN-17 |
| Correo inexistente de formato válido | «Correo o contraseña incorrectos» | Mismo comportamiento de rechazo y bloqueo |
| Cuenta inactiva con credenciales válidas | «Correo o contraseña incorrectos» | Mismo mensaje sin revelar el estado |

Los mensajes de credenciales se muestran como error general; los de campo se asocian a su campo. Los campos vacíos no se describen como credenciales verificadas incorrectas. No hay mensaje de éxito de ingreso adicional: el éxito crea la sesión y redirige al inicio o al destino interno permitido, donde se vuelve a comprobar el permiso del rol.

**Corrección de literal, no cambio de límite:** la traducción por defecto decía «menos de 254», aunque aceptaba 254. El mensaje final dice «como máximo 254» y coincide con el CA y el validador. Se verificaron 254/255, espacios exteriores, obligatoriedad, formato y caracteres nulos en cuatro pruebas `identity.test_audit01k_literals` sin utilizar base de datos. Esas pruebas no sustituyen el recorrido visual final.

## Bloqueo vinculado a HU-AUTH-02/CA-01..03 y CP-HU-AUTH-02-001

En el quinto fallo consecutivo de credenciales y durante el plazo activo se muestra exactamente «Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {minutos} minuto(s).». `{minutos}` es el entero de minutos restantes redondeado hacia arriba, mínimo 1 mientras quede tiempo. El quinto fallo inicia 15 minutos. Los reintentos bloqueados no extienden el plazo ni conceden acceso con una clave correcta. Otra sesión comparte el mismo bloqueo del identificador normalizado; no bloquea otras cuentas.

Al vencer, credenciales válidas crean sesión y restablecen el contador a cero. Un ingreso válido anterior al quinto fallo también corta la serie de fallos consecutivos. La protección es por identificador conforme RN-17, no un límite agregado por IP. Una sesión que ya estaba autenticada no se transforma por este flujo en un cierre remoto; el cierre/sesión única pertenece a las HU correspondientes de etapa 02.

## Denegación vinculada a HU-AUTH-01/CA-04 y CP-HU-AUTH-01-003

Una petición directa de un rol sin permiso devuelve 403 sin datos protegidos ni mutación de negocio. La página de denegación muestra:

- Título: «Acceso denegado · Minimarket».
- Estado: «Acceso denegado».
- Encabezado: «No tienes permiso para esta operación».
- Explicación: «Tu cuenta no tiene autorización para realizar esta operación.».
- Enlace: «Volver a mi inicio», destino `/inicio/`.

Un visitante ante una operación protegida se dirige a ingreso y no ve el contenido protegido. En particular, CP-HU-AUTH-01-003 especifica vendedor→alta de producto, almacenero→cobro, administrador→apertura de caja y visitante→historial; comprobar GET/POST con CSRF y conservación de productos, ventas, turnos y lotes poblados. La ausencia de botón por sí sola no verifica este criterio.

## Distinción de alcance que debe acompañar el cierre

El prompt `01_Ingreso_y_bloqueo.md` delimita AUTH-01/02 (siete CA) y permisos como condición de ingreso. `02_Sesion_y_personal.md` delimita AUTH-03/04a/04b/05, USR-01..06 y LOG-01 según selección. Por tanto, cerrar etapa 01 no prueba toda la gestión de empleados ni cambia las historias futuras. Los menús y operaciones de destino deben enlazarse a sus HU, sin declarar aprobada su lógica comercial por haber accedido desde login.

Los rechazos técnicos de CSRF (403), métodos no admitidos (405), direcciones inexistentes (404), cookies y destino seguro ya tienen pruebas de servidor, pero requieren su especificación literal cuando se incluyan en la demostración y se anuncie cierre de todos los mensajes posibles. No convertir esas pruebas técnicas en afirmación de revisión visual universal.
