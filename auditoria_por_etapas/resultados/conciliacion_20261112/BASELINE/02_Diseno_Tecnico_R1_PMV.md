# 2. Diseño técnico de `R1-PMV`

> **Actualización 05/11/2026:** Diseño propuesto para Sprint 1; algunas decisiones y permisos han cambiado. Compare con el código y la guía actual antes de usarlos como descripción del sistema. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Estado:** línea base técnica producida mediante una simulación de revisión de los seis Developers. Es una propuesta ejecutable para Jira, pero no acredita una reunión, aprobación ni implementación real. Los participantes deberán ratificarla en el Sprint Planning y Jira conservará el estado real.
>
> **Alcance:** únicamente las 9 Stories y 40 Story Points de Sprint 1. Las decisiones técnicas de este documento no agregan una décima historia ni Story Points; se implementan como Tasks transversales y Subtasks de las Stories existentes.
>
> **Fecha de corte documental:** 10 de octubre de 2026. Todos los resultados de pruebas, despliegues, backups y restauraciones permanecen `Pendientes` hasta que exista evidencia real.

## 2.1 Objetivo y principios

La solución será una aplicación web interna para una sola bodega, una sola caja física y hasta una operación de cobro a la vez. Debe permitir el recorrido:

`ingreso → producto → carga inicial por lotes → apertura de caja → preparación → cobro → constancia interna → cierre`

El diseño adopta estos principios:

1. **Monolito modular:** un despliegue y una base de datos, con límites claros entre identidad, catálogo, inventario, caja, ventas y constancias.
2. **Reglas en servidor:** la interfaz ayuda al usuario, pero la API/servicio y la base de datos vuelven a validar autorización e integridad.
3. **Dinero decimal y operaciones atómicas:** ningún importe usa punto flotante y ningún cobro puede quedar guardado a medias.
4. **Historial inmutable:** una venta confirmada y su constancia conservan los datos existentes en el momento del cobro.
5. **Reproducibilidad:** una base vacía puede construirse mediante migraciones y datos ficticios idempotentes.
6. **Evidencia honesta:** este documento especifica qué comprobar; `03` planifica las pruebas y `04` registra solamente resultados realmente obtenidos.

## 2.2 Decisiones de la línea base

Estas decisiones permiten completar la simulación. Su estado es **«acuerdo de simulación; requiere ratificación humana»** hasta que el acta de Planning y Jira registren la conformidad real.

| ID | Decisión adoptada para la línea base | Razón y efecto |
|---|---|---|
| `DT-01` | Aplicación web interna, responsiva para escritorio, servida bajo un solo origen | Reduce superficie de despliegue, CORS y manejo de sesión |
| `DT-02` | Monolito modular con Python 3.12/3.13, Django 5.2 LTS y plantillas Django; HTMX es opcional | Permite entregar el recorrido sin mantener SPA y API separadas |
| `DT-03` | PostgreSQL 17, ORM y migraciones nativas de Django; SQL explícito solo para locks, índices parciales y restricciones que el ORM no exprese | Conserva transacciones y restricciones verificables |
| `DT-04` | Tres cuentas ficticias separadas, cada una con exactamente un rol: `ADMIN`, `ALMACENERO` o `VENDEDOR` | Evita introducir cuentas multirrol no contempladas por las HU |
| `DT-05` | Sesión de Django almacenada del lado servidor, cookie `HttpOnly`, `Secure` en red, `SameSite=Lax`, protección CSRF y contraseña con Argon2id | La sesión puede invalidarse realmente y no depende de ocultar menús |
| `DT-06` | En R1-PMV todos los productos enlatados controlan vencimiento y todo lote exige una fecha posterior al día de negocio de Lima | Elimina el caso contradictorio de producto sin vencimiento dentro del Sprint 1 |
| `DT-07` | Número comercial de lote: texto recortado, normalizado a mayúsculas y único por producto. FEFO desempata por vencimiento, `received_at` y finalmente UUID interno | Evita depender del orden ambiguo de textos como `L2` y `L10` |
| `DT-08` | Importes y totales a 2 decimales; costo unitario/promedio interno a 4; redondeo comercial `ROUND_HALF_UP`; precios incluyen IGV | Evita errores binarios y conserva precisión de costo |
| `DT-09` | Salir está permitido con turno abierto; el turno continúa ligado al vendedor y todo borrador activo se descarta explícitamente sin tocar caja ni stock | Satisface `HU-AUTH-03` sin cerrar silenciosamente el turno |
| `DT-10` | Una caja sembrada y un solo turno global abierto; la unicidad se protege en PostgreSQL y no solo en la interfaz | Dos solicitudes simultáneas no pueden crear dos turnos |
| `DT-11` | La venta en preparación se persiste como borrador: la primera línea válida crea el único borrador `ACTIVE` y quitar la última lo descarta; agregar o quitar líneas no descuenta lotes | Evita un borrador activo vacío, hace observable el bloqueo de cierre y permite descartar el borrador de forma explícita |
| `DT-12` | Correlativo global `V-00000001`, monotónico, único e inmutable; se reserva dentro de la transacción confirmada | Un reintento no crea otro número y un rollback no deja una venta parcial |
| `DT-13` | Docker Compose para local/demostración; tres ambientes lógicos: local, CI efímero y demostración Linux; PostgreSQL nunca se publica a Internet | Misma construcción y migración en todos los ambientes |
| `DT-14` | Backup lógico en formato custom: 7 copias diarias y 4 semanales, manifiesto y SHA-256; restauración ensayada en una base limpia | Convierte recuperación en un resultado comprobable separado del backup |
| `DT-15` | Volumen posterior de referencia: 2 000 productos, 20 000 lotes y 300 ventas por día | Se prueba después del recorrido funcional y no bloquea su implementación |

Las versiones de parche de Python y dependencias se fijan en los archivos de dependencias y en el lockfile o mecanismo equivalente. Su actualización exige Pull Request y pipeline exitoso; no se cambia de versión mayor durante el Sprint.

## 2.3 Arquitectura y módulos

```text
Navegador de caja/administración
        │ mismo origen + cookie de sesión + CSRF
        ▼
Django 5.2 (monolito modular)
  ├─ identity     cuentas, sesión y autorización
  ├─ catalog      categorías y productos
  ├─ inventory    cargas, lotes y movimientos
  ├─ cash         caja, turnos y movimientos de efectivo
  ├─ sales        borrador, cobro, FEFO, idempotencia y constancia
  └─ app_platform salud, auditoría y configuración compartida
        │ transacciones y constraints
        ▼
PostgreSQL 17 ─────► backup cifrado fuera del repositorio
```

Los módulos se comunican mediante servicios de aplicación dentro del mismo proceso. Las vistas no escriben directamente en modelos de otro módulo. No se incorporan microservicios, colas, caché distribuida ni sincronización offline en R1-PMV.

### Contrato entre capas

| Capa | Responsabilidad | No debe hacer |
|---|---|---|
| Plantillas/HTMX | Formularios, estados de carga, mensajes, foco, navegación y validación de ayuda | Decidir permisos, stock, importes finales o correlativos |
| Vista/controlador Django | Autenticar, validar forma de entrada, invocar un caso de uso y mapear la respuesta HTTP | Ejecutar reglas transaccionales dispersas |
| Servicio de aplicación | Autorizar la acción, aplicar RN, abrir transacción, definir locks y producir DTOs | Confiar en totales calculados por el navegador |
| Dominio/modelos | Tipos, estados y operaciones válidas | Depender de HTML o de la sesión del navegador |
| PostgreSQL | Unicidad, FK, checks, locks, atomicidad e índices | Sustituir mensajes de negocio o autorización por rol |

## 2.4 Matriz de roles y autorización

Cada cuenta posee un solo rol. La ausencia de permiso produce `403` aunque se invoque una URL directamente. Una sesión inexistente o revocada produce redirección al ingreso para navegación HTML y `401` para solicitudes técnicas.

| Operación de R1-PMV | `ADMIN` | `ALMACENERO` | `VENDEDOR` | Restricción adicional |
|---|:---:|:---:|:---:|---|
| Iniciar/cerrar su propia sesión | Sí | Sí | Sí | Solo cuenta activa |
| Registrar producto enlatado | Sí | No | No | Código único y categoría sembrada |
| Ejecutar carga inicial por lotes | No | Sí | No | Solo una vez por producto |
| Abrir caja | No | No | Sí | No puede existir otro turno abierto |
| Preparar/cobrar venta | No | No | Sí | Debe ser dueño del turno abierto |
| Consultar constancia de la venta | Sí | No | Sí | El vendedor solo consulta sus propias ventas; el administrador puede consultar todas |
| Cerrar caja | No | No | Sí | Solo el dueño del turno y sin borrador activo |

Los permisos se verifican con decoradores/mixins y nuevamente en el servicio usando el usuario autenticado. Nunca se acepta desde el cliente un `seller_id`, `account_id`, `shift_id` o rol como autoridad.

## 2.5 Modelo lógico de datos

Todos los identificadores de negocio usan UUID salvo el contador correlativo. Los timestamps se almacenan como `timestamptz` en UTC. Las FK históricas utilizan `PROTECT` o una política equivalente; R1-PMV no expone borrado físico de cuentas, productos, lotes, turnos ni ventas.

| Entidad lógica | Campos mínimos | Integridad principal |
|---|---|---|
| `role` | código `ADMIN`, `ALMACENERO` o `VENDEDOR`, nombre | código único; `CHECK` limita los tres códigos y exactamente tres filas se siembran en R1 |
| `account` | UUID, nombre, correo original/normalizado, hash, rol, activo, fechas | correo normalizado único; una FK de rol obligatoria; hash nunca reversible |
| `django_session` | clave opaca, datos de sesión y vencimiento | cookie contiene solo identificador opaco; revocación al salir |
| `category` | UUID, nombre, nombre normalizado, activo | nombre normalizado único; seed «Productos enlatados» |
| `product` | UUID, categoría, nombre, código normalizado, unidad, precio con IGV, mínimo, `controls_expiration` (controla vencimiento), costo promedio, fechas | código único; precio `> 0`; mínimo entero `>= 0`; costo `>= 0`; `CHECK` exige control de vencimiento en R1 |
| `initial_inventory_load` | UUID, producto, responsable, fecha | `product_id` único: una sola carga inicial |
| `lot` | UUID, producto, carga, número original/normalizado, cantidad inicial/disponible, costo unitario, vencimiento, ingreso | lote normalizado único por producto; `0 <= disponible <= inicial`; cantidad y costo positivos |
| `inventory_movement` | UUID, producto, lote, tipo, cantidad con signo, referencia, responsable, fecha | append-only; en R1 tipos `INITIAL_LOAD` y `SALE` |
| `cash_register` | UUID, código, activo | seed de una caja `CAJA-01`; no hay pantalla para crear otra |
| `cash_shift` | UUID, caja, vendedor, apertura, monto inicial, estado, cierre, esperado, contado, diferencia | índice único parcial de turno `OPEN`; importes no negativos donde corresponda |
| `sale_draft` | UUID, turno, vendedor, estado, creación/actualización/descarte | máximo un borrador `ACTIVE` por turno; solo para turno abierto y mismo vendedor; un `ACTIVE` siempre tiene al menos una línea |
| `sale_draft_line` | borrador, producto, cantidad, precio informativo | cantidad entera positiva; producto único por borrador; no reserva ni descuenta stock |
| `sale_number_counter` | clave singleton, último valor | fila bloqueada al confirmar; produce `V-` + 8 dígitos |
| `idempotency_record` | operación, UUID de idempotencia, actor, hash de solicitud, estado, referencia/resultado, fechas | único por operación y clave; una clave con contenido distinto se rechaza |
| `sale` | UUID, correlativo, turno, vendedor, snapshots de vendedor/caja, base, IGV, total, efectivo, vuelto, fecha, estado | correlativo único; dinero exacto; venta confirmada inmutable |
| `sale_item` | venta, producto, snapshots de nombre/código/unidad, cantidad, precio, costo promedio, importe | cantidad positiva; precio/costo históricos; importe exacto |
| `sale_lot_allocation` | detalle, lote, cantidad | cantidad positiva; par detalle/lote único; demuestra FEFO |
| `cash_movement` | turno, tipo, importe con signo, estado, venta opcional, fecha | una venta genera un solo movimiento confirmado; diseño extensible a movimientos futuros |
| `audit_event` | fecha, actor, acción, entidad/referencia, resultado, request ID, metadatos no sensibles | append-only; nunca contiene contraseña, cookie, CSRF ni efectivo entregado completo |
| `django_migrations` | aplicación, migración y fecha | control nativo de la versión aplicada |

### Relaciones principales

```text
role 1 ── N account
account 1 ── N initial_inventory_load 1 ── N lot
category 1 ── N product 1 ── N lot
product  1 ── N inventory_movement

account(VENDEDOR) 1 ── N cash_shift N ── 1 cash_register
cash_shift 1 ── N sale_draft 1 ── N sale_draft_line
cash_shift 1 ── N sale 1 ── N sale_item 1 ── N sale_lot_allocation
lot 1 ── N sale_lot_allocation
cash_shift 1 ── N cash_movement
```

Un turno puede acumular borradores históricos confirmados o descartados, pero `DB-C10` garantiza que como máximo uno permanezca `ACTIVE` al mismo tiempo. El servicio crea ese estado en la misma transacción que la primera línea válida y lo cambia a `DISCARDED` al retirar la última; por tanto no persiste un `ACTIVE` vacío ni puede bloquear el cierre sin una venta en preparación real.

### Tipos numéricos y fórmulas

- Precio, base, IGV, total, efectivo, vuelto, apertura, esperado, contado y diferencia: `numeric(14,2)` o `Decimal` equivalente.
- Costo unitario, costo promedio y snapshot de costo: `numeric(14,4)`.
- Cantidades: enteros; R1 no vende por peso.
- Nunca se usan `float`/`double` para dinero.
- Redondeo: `ROUND_HALF_UP` únicamente en los límites definidos.
- Total de línea: `cantidad × precio_con_igv`, redondeado a 2 decimales.
- Total de venta: suma exacta de importes de línea.
- Base imponible: `ROUND_HALF_UP(total / 1.18, 2)`.
- IGV: `total - base`; esta resta garantiza `base + IGV = total`.
- Costo promedio inicial: `ROUND_HALF_UP(Σ(cantidad_lote × costo_unitario_lote) / Σ(cantidad_lote), 4)`.
- Efectivo esperado: `monto_inicial + Σ(movimientos_de_caja_confirmados.importe_con_signo)`. En R1 cada venta en efectivo confirmada aporta `+total`; el diseño admite movimientos y anulaciones futuras sin cambiar la fórmula.
- Diferencia de cierre: `dinero_contado - dinero_esperado`.

### Restricciones e índices mínimos

| ID | Restricción o índice | Motivo |
|---|---|---|
| `DB-C01` | `UNIQUE(account.email_normalized)` | Login inequívoco |
| `DB-C02` | `UNIQUE(category.name_normalized)` | Seed idempotente y sin categorías duplicadas |
| `DB-C03` | `UNIQUE(product.barcode_normalized)` | Código de barras irrepetible |
| `DB-C04` | checks de precio `> 0`, mínimo `>= 0`, costo `>= 0` | Integridad aunque se evada el formulario |
| `DB-C05` | `UNIQUE(initial_inventory_load.product_id)` | Impide segunda carga inicial, incluso concurrente |
| `DB-C06` | `UNIQUE(lot.product_id, lot.number_normalized)` | Alcance de unicidad del lote acordado |
| `DB-C07` | checks `initial_qty > 0`, `0 <= available_qty <= initial_qty`, `unit_cost > 0` | Evita stock negativo o lote vacío |
| `DB-C08` | índice FEFO `(product_id, expiration_date, received_at, id)` condicionado a `available_qty > 0` | Selección estable de lotes vendibles |
| `DB-C09` | índice único parcial de `cash_shift(register_id)` donde estado=`OPEN` | Una sola caja abierta bajo carrera |
| `DB-C10` | índice único parcial de `sale_draft(shift_id)` donde estado=`ACTIVE` | Un borrador activo observable |
| `DB-C11` | `UNIQUE(sale.number)` y `UNIQUE(idempotency_record.operation, key)` | Correlativo e idempotencia |
| `DB-C12` | `UNIQUE(cash_movement.sale_id)` cuando hay venta | Un cobro no suma dos veces a caja |
| `DB-C13` | índices de búsqueda por código, nombre normalizado, turno/fecha de venta y vencimiento | Volumen de referencia y consultas del flujo |
| `DB-C14` | FK restrictivas desde ventas, detalles, asignaciones, lotes y turnos | Protege historial |
| `DB-C15` | `CHECK(role.code IN ('ADMIN','ALMACENERO','VENDEDOR'))` | Impide roles fuera de los tres autorizados en R1 |
| `DB-C16` | `CHECK(product.controls_expiration = TRUE)` en R1 | Impide crear un producto enlatado sin control de vencimiento |

La condición «vencimiento posterior al día actual de Lima» y las sumas entre filas no se expresan como `CHECK` dependiente del reloj. Se validan dentro del servicio transaccional con un reloj inyectable y se cubren con pruebas de integración. Las restricciones simples sí viven en PostgreSQL.

## 2.6 Tiempo, lote y existencias

- Toda escritura usa UTC; la pantalla muestra `America/Lima`.
- El **día de negocio** se obtiene en el servidor con zona `America/Lima`; no se confía en la hora del navegador.
- Un lote es vendible solamente si `expiration_date > business_date` y `available_qty > 0`.
- `received_at` se asigna en el servidor al confirmar la carga y queda inmutable.
- El número comercial de lote se recorta y normaliza a mayúsculas antes de validar unicidad. Se conserva también el texto normalizado que se muestra.
- Orden FEFO: `expiration_date ASC, received_at ASC, id ASC`.
- Existencia física: suma de `available_qty` de todos los lotes.
- Existencia vendible: suma de lotes con saldo y vencimiento posterior al día de Lima.

## 2.7 Transacciones, concurrencia e idempotencia

### Orden global de locks

Para reducir deadlocks, cada caso de uso bloquea siempre en este orden cuando corresponda:

`registro de idempotencia (solo en cobro) → turno → productos ordenados por UUID → lotes en orden FEFO → contador correlativo → registros derivados`

Una transacción que detecte deadlock o error de serialización puede reintentarse como máximo dos veces; una validación de negocio no se reintenta. Todo fallo termina en rollback y un mensaje general con `request_id`.

### Carga inicial

1. Autoriza rol `ALMACENERO`.
2. Inicia `transaction.atomic()` y bloquea el producto con `SELECT ... FOR UPDATE`.
3. Comprueba que no exista `initial_inventory_load`.
4. Valida todos los lotes, incluidos número normalizado, cantidades, costo y vencimiento.
5. Inserta cabecera, lotes y movimientos; calcula el costo promedio inicial.
6. Si una fila falla, revierte toda la carga. La restricción `UNIQUE(product_id)` decide de forma segura dos intentos simultáneos.

### Apertura de caja

1. Autoriza `VENDEDOR` y valida monto decimal no negativo.
2. Bloquea la caja sembrada.
3. Revalida que no exista turno abierto y crea el turno.
4. El índice único parcial protege contra dos aperturas simultáneas; la solicitud perdedora recibe conflicto de negocio y no un error técnico sin tratar.

### Preparación de venta

- Agregar la primera línea válida crea atómicamente el único borrador `ACTIVE`; crear o modificar sus líneas valida turno abierto, vendedor dueño, cantidad entera positiva y existencia vendible informativa.
- Al quitar la última línea, la operación marca el borrador como `DISCARDED` dentro de la misma transacción. No existe un borrador `ACTIVE` vacío; iniciar la pantalla sin líneas no crea uno.
- El borrador no reserva ni descuenta lotes. Precio, impuesto y stock se recalculan al confirmar.
- Cerrar caja consulta en servidor si existe un borrador `ACTIVE` con líneas; el estado de una pestaña no es autoridad.

### Cobro

1. Exige cabecera `Idempotency-Key` UUID y calcula un hash canónico del turno, líneas y efectivo.
2. Crea/bloquea el registro de idempotencia. Misma clave + mismo hash devuelve la venta original; misma clave + otro hash responde conflicto.
3. Bloquea el turno y confirma que sigue abierto, pertenece al vendedor y coincide con el borrador.
4. Bloquea productos por UUID y lotes vendibles en orden FEFO.
5. Recalcula precios, base, IGV, total, efectivo, vuelto y stock; nunca acepta totales del cliente.
6. Reserva el siguiente contador y genera `V-00000001` dentro de la misma transacción.
7. Inserta venta, snapshots, asignaciones FEFO, movimientos de inventario y un movimiento de caja por el total neto.
8. Decrementa lotes sin permitir valores negativos, marca el borrador confirmado y completa la idempotencia.
9. Cualquier error revierte venta, stock, caja, contador y borrador confirmado.

### Cierre de caja y carrera con cobro

1. La operación bloquea el turno y revalida vendedor, estado `OPEN` y ausencia de borrador `ACTIVE`.
2. Calcula el esperado desde movimientos confirmados y valida contado decimal no negativo.
3. Guarda esperado, contado, diferencia y fecha; cambia a `CLOSED` una sola vez.
4. Si el cobro obtiene primero el lock, termina y entra en el esperado. Si el cierre obtiene primero el lock, cierra y el cobro posterior se rechaza sin modificar nada.
5. Toda repetición posterior al cierre informa que el turno ya está cerrado, no crea otra acta y no altera la original.

### Logout

Si existe un borrador con líneas, esta operación solo se invoca después de la confirmación explícita exigida por `HU-AUTH-03`; cancelar no envía la orden ni modifica datos. Al confirmar, dentro de una operación atómica se marca el borrador como `DISCARDED`, se registra el evento y se elimina la sesión. Sin borrador, la confirmación de salida solo revoca la sesión. No se cierra el turno, no se descuenta stock y no se cambia el efectivo. El HTML posterior no puede recuperarse como contenido autenticado desde la caché.

## 2.8 Contratos web mínimos

Las rutas son nombres de contrato y pueden implementarse como vistas Django HTML/HTMX. Las respuestas parciales y completas deben preservar las mismas reglas.

| Método y ruta lógica | Rol | Entrada autoritativa | Resultado observable |
|---|---|---|---|
| `POST /login` | Público | correo, contraseña, CSRF | sesión rotada o mensaje general idéntico |
| `POST /logout` | Autenticado | CSRF y confirmación de descarte cuando exista borrador con líneas | borrador descartado si corresponde, sesión revocada y pantalla limpia |
| `POST /products` | ADMIN | ficha del producto | producto con stock cero o errores por campo/conflicto |
| `POST /products/{id}/initial-load` | ALMACENERO | uno o varios lotes | carga completa o ninguna fila |
| `POST /cash-shifts/open` | VENDEDOR | monto inicial | turno abierto o conflicto de caja única |
| `GET /sales/draft` | VENDEDOR | sesión | borrador con líneas del turno propio, o preparación vacía sin crear borrador |
| `POST/PATCH /sales/draft/lines` | VENDEDOR | producto/cantidad | primera línea crea borrador, quitar la última lo descarta; lista y totales informativos, sin descuento |
| `POST /sales/checkout` | VENDEDOR | líneas, efectivo, idempotencia | venta confirmada, vuelto y correlativo |
| `GET /sales/{number}/receipt` | VENDEDOR | número de venta | DTO histórico sin costo de compra |
| `POST /cash-shifts/{id}/close` | VENDEDOR | contado | acta con esperado/diferencia o bloqueo por borrador activo con líneas |
| `GET /health/live` | Plataforma | ninguna | proceso disponible, sin datos internos |
| `GET /health/ready` | Plataforma restringida | autenticación de infraestructura | aplicación y BD listas |

Errores esperados: `400` formato inválido, `401` sin sesión, `403` rol/propiedad incorrectos, `404` recurso no visible, `409` estado concurrente o duplicado y `422` regla de negocio. Ningún error devuelve stack trace, SQL, existencia de correo, hash o secreto.

## 2.9 Seguridad

1. Correo normalizado con `strip` + minúsculas y consulta de tiempo comparable para evitar revelar cuentas.
2. Hash Argon2id mediante el sistema de hashers de Django; nunca se guardan ni registran claves en texto claro.
3. Rotación de identificador de sesión al ingresar y eliminación al salir.
4. Cookie `HttpOnly`, `SameSite=Lax`, `Secure` en demostración; expiración coherente y no almacenamiento del token en `localStorage`.
5. CSRF obligatorio en toda escritura y política de mismo origen.
6. Autorización server-side por rol, propiedad del turno y estado del recurso.
7. Validación Django de longitud, tipo, límites y listas permitidas; escape de plantillas por defecto. Ningún SQL concatena entrada.
8. Cabeceras mínimas: HSTS cuando exista HTTPS estable, `X-Content-Type-Options`, `Referrer-Policy`, política de marcos y CSP compatible con HTMX sin `unsafe-eval`.
9. Límite de solicitudes al login por IP/sesión como defensa técnica. El bloqueo funcional de cuenta de `HU-AUTH-02` no se adelanta a Sprint 1.
10. Secretos por variables/secret store; `.env.example` contiene nombres, nunca valores reales. PostgreSQL solo acepta red interna.
11. Logs redactan `password`, cookies, CSRF, claves de idempotencia completas y datos de conexión.
12. Dependencias se auditan en CI; una vulnerabilidad crítica o alta explotable bloquea el despliegue hasta evaluación registrada.

## 2.10 Migraciones y datos iniciales

- Las migraciones Django son versionadas, revisadas y aplicadas automáticamente; no se modifica una migración que ya llegó a demostración.
- `RunSQL` se usa solamente para índices parciales, checks o triggers justificados, con operación inversa cuando sea segura.
- CI crea PostgreSQL vacío, ejecuta todas las migraciones, aplica seeds dos veces y confirma que la segunda ejecución no duplica filas.
- El comando idempotente de datos ficticios crea roles, tres cuentas de prueba, categoría «Productos enlatados», caja `CAJA-01` y contador inicial. Las contraseñas proceden del ambiente y no del repositorio.
- El reset de prueba solo puede ejecutarse en ambientes marcados expresamente como `local` o `ci`; debe negarse en demostración.
- No se cargan productos, lotes, ventas ni cierres ficticios como si fueran evidencia del Sprint. Los fixtures de prueba permanecen identificados como tales.

## 2.11 Ambientes, CI y despliegue

| Ambiente | Datos | Acceso | Propósito |
|---|---|---|---|
| Local | Fixtures ficticios reiniciables | Equipo | Desarrollo y prueba individual |
| CI | PostgreSQL efímero por ejecución | Pipeline | Migraciones, análisis y pruebas automáticas |
| Demostración | Datos ficticios controlados | HTTPS y equipo autorizado | Revisión integrada y Sprint Review |

### Pipeline obligatorio

1. Instalación reproducible de dependencias fijadas.
2. Formato/lint y comprobaciones estáticas.
3. `python manage.py check --deploy` con configuración de demostración segura.
4. Base vacía → migraciones → seeds dos veces → comprobación de drift.
5. Pruebas unitarias e integración con el runner estándar `python manage.py test`; no se agrega otro runner durante el Sprint salvo acuerdo del equipo.
6. Pruebas de concurrencia e idempotencia contra PostgreSQL real, no SQLite.
7. Construcción de imagen identificada por commit.
8. Playwright del recorrido crítico en ambiente efímero o de integración.
9. Publicación del artefacto solo si todas las puertas anteriores terminan correctamente.

### Despliegue y reversión

- El despliegue de demostración es manual y autorizado desde un artefacto ya comprobado en CI.
- Antes de una migración con datos se crea backup y manifiesto.
- Se aplica migración una sola vez, se inicia la nueva imagen y se ejecuta smoke test: `ready`, login, lectura de categoría y acceso autorizado.
- Si falla la aplicación, se vuelve a la imagen anterior. Una migración destructiva queda prohibida en Sprint 1; los cambios de esquema son aditivos para permitir reversión de aplicación o, en caso extremo, restauración controlada.
- La base no expone puerto público. HTTPS es obligatorio si el enlace sale del equipo local.

## 2.12 Observabilidad y auditoría

- Logs estructurados con UTC, nivel, evento, `request_id`, usuario interno cuando exista, módulo, duración y resultado.
- Cada respuesta de error muestra un `request_id` que permite correlacionar sin revelar internals.
- Eventos mínimos: login exitoso/fallido sin contraseña, logout, producto creado/rechazado, carga confirmada/rechazada, apertura/conflicto, cobro/rollback/reintento idempotente y cierre/conflicto.
- Métricas mínimas del host: disponibilidad de aplicación, conexión a BD, latencia y conteo de respuestas 5xx. Observabilidad avanzada queda fuera del PMV.
- El registro de auditoría no sustituye las evidencias de prueba y no se marca como implementado hasta existir una ejecución real.

## 2.13 Backup y restauración

### Backup (`S1-OPS-DB-01`)

1. Ejecutar `pg_dump` en formato custom, sin propietarios ni credenciales embebidas.
2. Nombrar el archivo con ambiente y timestamp UTC.
3. Generar manifiesto con versión PostgreSQL, commit, última migración, tamaño y conteos de control.
4. Calcular SHA-256 y almacenarlo junto al manifiesto.
5. Guardar la copia cifrada fuera del repositorio y del volumen activo de PostgreSQL.
6. Conservar 7 diarias y 4 semanales. Ninguna eliminación se ejecuta durante la simulación documental.

### Restauración (`S1-OPS-DB-02`)

1. Crear una base limpia aislada con la misma versión mayor.
2. Verificar checksum antes de restaurar.
3. Ejecutar `pg_restore`, comprobar migraciones y ejecutar checks de integridad.
4. Comparar conteos del manifiesto y verificar correlativos, un turno, productos, lotes y una constancia histórica.
5. Ejecutar el recorrido de smoke test sin afectar demostración.
6. Registrar duración y resultado real en `04_Evidencias.md`; hasta entonces el estado es `Pendiente`.

Objetivos propuestos para el piloto: **RPO máximo 24 horas** y **RTO máximo 2 horas**. La puerta de piloto exige una restauración real satisfactoria, no solo la existencia de un archivo.

## 2.14 Requisitos no funcionales de R1-PMV

| ID | Requisito verificable | Método previsto |
|---|---|---|
| `NFR-01` | Ninguna operación transaccional deja venta, stock, caja o carga a medias | Fallos inducidos e inspección posterior |
| `NFR-02` | Doble solicitud no crea dos cargas, turnos, ventas, correlativos ni cierres | Pruebas concurrentes con barrera |
| `NFR-03` | Toda operación protegida rechaza sesión ausente, rol incorrecto y URL directa | Matriz de autorización automática/manual |
| `NFR-04` | Dinero usa decimal exacto; `base + IGV = total`; stock nunca es negativo | Pruebas de frontera y constraints |
| `NFR-05` | En volumen de referencia, búsqueda responde en ≤ 2 s p95 y cobro en ≤ 3 s p95 en el host de demostración acordado | Ensayo repetible, ambiente y muestra registrados |
| `NFR-06` | Flujo principal operable con teclado, foco visible, etiquetas y mensajes asociados al campo | Revisión manual y Playwright básico |
| `NFR-07` | Compatible con Chrome estable en Windows 10/11 a 1366×768 como mínimo; una comprobación en Edge queda como uso de reserva, no como puerta de R1 | Matriz manual registrada |
| `NFR-08` | Instalación, migración, seeds y build son reproducibles desde un clon limpio | Pipeline y guía repetida por otro Developer |
| `NFR-09` | Logs permiten correlacionar fallos sin incluir secretos ni datos sensibles | Inspección de logs de casos positivos/negativos |
| `NFR-10` | Backup cumple checksum/retención y restore recupera el recorrido en ≤ 2 h | Ejecución separada de backup y restore |
| `NFR-11` | Fechas se almacenan en UTC y reglas de vencimiento/visualización usan Lima | Pruebas alrededor de medianoche de Lima |
| `NFR-12` | Una venta y constancia confirmadas permanecen inmutables aunque cambien datos maestros | Consulta histórica después de modificar fixture maestro |

Los umbrales de rendimiento son una línea base de aceptación para la demostración, no una promesa de producción. El reporte debe incluir equipo, versión, datos, número de ejecuciones y percentil; una afirmación sin esos datos no constituye evidencia.

## 2.15 Revisión simulada de los seis Developers

Esta tabla documenta el razonamiento de la simulación; no se presenta como participación humana real.

| Perfil simulado | Perspectiva revisada | Defecto que debía evitarse | Resultado incorporado |
|---|---|---|---|
| Des.1 - Velasquez | Datos, inventario y concurrencia | Dos cargas iniciales, FEFO inestable y stock negativo | locks por producto/lote, unicidad de carga, índice FEFO y ledger |
| Des.2 - Nolasco | Servicios, autenticación y seguridad | Permisos solo visuales, sesión reutilizable o cobro parcial | autorización server-side, sesión revocable, CSRF y atomicidad |
| Des.3 - Castillo | UI/HTMX y accesibilidad | Totales autoritativos en navegador o formulario inutilizable por teclado | recálculo servidor, estados de error, foco y etiquetas |
| Des.4 - Alcalde | Caja, integración y operación | Dos turnos, carrera cobro/cierre o despliegue irrepetible | índice parcial, lock de turno, Compose y smoke test |
| Des.5 - Walter Luis Colonia Infantas | Datos iniciales y automatización | seeds duplicados o pruebas contra SQLite que oculten fallos | seeds idempotentes y CI contra PostgreSQL real |
| Des.6 - Angeles | QA, constancia y recorrido | constancia mutable, costo expuesto o backup sin restore | snapshots, DTO sin costo, E2E y restauración independiente |

La simulación concluye que el diseño es **implementable dentro del alcance**, sujeto a las 67 Tasks/Subtasks y 216 horas de `16_Task_Breakdown.md`, y deja 24 horas de reserva. Esta conclusión es un pronóstico que los seis Developers reales deben ratificar; no prueba que el sistema ya exista.

## 2.16 Puertas técnicas

Antes de comenzar una Story:

- sus CA y RN están trazados en `03`;
- las decisiones necesarias de esta línea base están ratificadas;
- existen contratos o fixtures que permitan trabajo paralelo;
- la Task/Subtask tiene resultado y evidencia esperada.

Antes de marcar una Story como Hecha:

- migraciones aplican desde base vacía;
- autorización, servicio y constraints relevantes están comprobados;
- pruebas automáticas y manuales asociadas tienen resultado real;
- un revisor distinto comprobó sus CA;
- no existen Bugs críticos/graves abiertos;
- `04_Evidencias.md` enlaza evidencia real, no una descripción futura.

Antes del piloto controlado, además:

- el recorrido E2E completo es satisfactorio;
- el despliegue y smoke test son satisfactorios;
- backup y restauración se ejecutaron por separado con checksum válido;
- la constancia exhibe la advertencia tributaria;
- existe autorización académica/documentada antes de un piloto, si el curso lo permite.

## 2.17 Fuera de alcance técnico del Sprint 1

- facturación electrónica, SUNAT, Yape y correo;
- recuperación/bloqueo funcional de cuentas;
- multirrol, varias sedes, varias cajas o ventas simultáneas en puestos distintos;
- productos sin vencimiento o por peso;
- reposiciones, mermas, anulaciones y movimientos manuales de caja;
- reportes, dashboards, PDF y configuración comercial;
- alta disponibilidad, réplica, sincronización offline y observabilidad avanzada.

El modelo puede admitir extensiones futuras, pero no se implementan pantallas ni reglas de esas historias durante Sprint 1.

## 2.18 Fuentes oficiales de compatibilidad

La selección de versiones se verificó contra documentación oficial en la fecha de corte. Estas fuentes justifican la línea base, pero los parches exactos deben fijarse en el archivo de dependencias y volver a comprobarse en CI:

- Django 5.2 es una versión LTS y declara compatibilidad con Python 3.13: <https://docs.djangoproject.com/en/5.2/releases/5.2/>.
- Calendario oficial de versiones soportadas de Django: <https://www.djangoproject.com/download/>.
- Ciclo oficial de soporte de PostgreSQL 17: <https://www.postgresql.org/support/versioning/>.
- Publicaciones oficiales de Python 3.13: <https://www.python.org/downloads/release/python-31316/>.
- Documentación oficial de HTMX 2.x: <https://htmx.org/docs/>.

Una actualización de parche dentro del Sprint solo se admite mediante Pull Request, pipeline verde y ausencia de impacto en migraciones o contratos. Cambiar una versión mayor o menor requiere ADR, reestimación y nueva ratificación de la línea base.

## Adenda de catálogo actual · DOC03-01 · 09/11/2026

**Vigencia:** esta adenda conserva el corte histórico de09/11; la selección posterior de PROD03 y su evidencia física están en [03-W](auditoria_por_etapas/resultados/anexos/ETAPA-03-W-conciliacion.md).

El usuario acepta productos de cualquier categoría activa, por unidad y con vencimiento obligatorio. DT-06 mantiene control obligatorio por lote y unidad UND; la categoría preparada de R1 es un ejemplo inicial y deja de ser la única categoría admisible. El modelo y las restricciones ya admitían categorías activas arbitrarias; esta ampliación no requiere migración ni retirar restricciones. El nombre interno de compatibilidad `register_canned_product` y el constraint `product_unit_und_in_r1` no limitan comercialmente a enlatados. ADMIN gestiona; ALMACENERO consulta; VENDEDOR consulta solo en su venta autorizada (DOC-00-14, instrucción del usuario). Edición/eliminación de categorías y escáner conservan su clasificación futura. [Trazabilidad y pruebas de alcance](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md).

**Adenda DOC03-02 (09/11/2026):** corrección de código ADMIN aceptada, identidad UUID estable, clave normalizada única y snapshots históricos conservados. Se documenta el contrato existente de formulario/servicio; no hay nueva migración. Para Barcode to PC Server se propone captura por emulación de teclado en el campo enfocado y perfil sin envío automático del formulario. No se presupone API, plugin de navegador ni driver dentro de Django. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-G-codigo-y-lector.md).


## Adenda técnica · políticas de producto03-I · 10/11/2026

minimum_stock tiene máximo999999 en formularios/modelo y CHECK persistente. search_name es UNIQUE: colapso de espacios, casefold y NFC, conservando acentos. Alta/edición comercial mediante servicios normaliza y guarda con savepoint; conflicto de código se vincula a barcode y de nombre a name, sin ocultar IntegrityError ajenos.

catalog.0005 examina nombres/mínimos; aborta ante conflictos sin fusionar ni recortar. Después recalcula claves y añade restricciones, conservando nombres visibles y referencias; una edición posterior normaliza espacios del nombre. SQL/QuerySet que cambien nombre sin actualizar la clave quedan fuera del contrato de servicios y requieren disciplina de escritura; UNIQUE protege la clave almacenada.

[Evidencia y límites03-I](auditoria_por_etapas/resultados/anexos/ETAPA-03-I-politicas.md).
