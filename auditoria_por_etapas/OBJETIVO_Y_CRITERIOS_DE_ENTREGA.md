# Objetivo común de la entrega académica por internet

**Vigente al 20/11/2026.** El profesor representa al dueño. La meta es demostrar el minimarket en una URL pública HTTPS, con el alcance de pagos fijado el 17/11. El proyecto académico puede utilizar recursos ya disponibles.

**Objetivo general:** entregar y demostrar un sistema de minimarket accesible mediante una URL pública HTTPS, con cuentas de administrador, almacenero y vendedor, que permita recorrer inventario → preparación → cobro en efectivo, Yape por QR o ambos → constancia e historial → control de caja y devoluciones, conservando dinero, stock y trazabilidad; cada comportamiento visible debe estar especificado en HU, CA y CP, y probado en el mismo build publicado.

La fuente funcional sigue siendo [08](../08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA). Este documento coordina el trabajo y no constituye una segunda especificación. El estado actual es **OBJETIVO ACEPTADO, ENTREGA NO VERIFICADA**. Una URL pública sin recorridos comprobados no es entrega aprobada; las pruebas locales tampoco son pruebas de publicación.

## Condiciones comprobables de terminación

1. **Acceso real por internet:** el profesor abre una URL HTTPS desde un equipo o red distintos al del desarrollador. La aplicación funciona sin depender de `localhost` ni de que esté encendido el servidor de desarrollo del estudiante. Se admite subdominio del proveedor; no se exige dominio de pago. Elegir servicio compatible con Django, almacenamiento persistente y base de datos, verificando las condiciones vigentes del plan gratuito o presupuesto antes de publicar.
2. **Recorrido de negocio completo:** abrir turno, consultar/recibir existencias, preparar venta, cobrar por los tres modos, recuperar constancia, consultar desglose y cerrar/conciliar. Inventario, ventas y dinero coinciden. Probar también rechazos y acciones de los otros roles.
3. **Yape comprobado.** El vendedor muestra el QR estático del receptor propio. El pagador introduce el monto. Demostrar por separado custodia y origen del aviso, transporte autenticado, ingreso en el receptor, asociación previa al pedido y aplicación única. La vía propuesta usa puente propio y desafío del cliente. Un aviso tardío, ambiguo o huérfano queda en revisión. El cajero no acredita por captura, importe o declaración.
4. **Dinero separado:** distinguir efectivo recibido/aplicado/vuelto, Yape recibido/aplicado, cobro pendiente, exceso no aplicado y devolución pendiente/confirmada. En una venta mixta no se suma dos veces el total. Yape no incrementa el efectivo esperado de la gaveta.
5. **Incidentes conservados:** cancelación antes de pagar, abandono después de un abono, duplicados, error de destinatario, pago tardío, falta de stock y fallo de red no deben borrar evidencia ni provocar un segundo cobro, devolución o descuento de stock. El estado debe permitir conocer lo que falta resolver.
6. **Trazabilidad exacta:** matriz HU→CA→CP→ruta/acción/literal→servidor→datos→evidencia del build público. Cada texto visible debe estar especificado palabra por palabra en08 o en un catálogo aceptado referenciado por sus CA y CP, con formato de variables; si falta, resolver esa brecha antes de implementar o aprobar la interfaz. Un comportamiento extra se corrige o se somete a decisión; nunca se acepta solo porque existe. Mantener los IDs y justificar cada cambio de criterio.
7. **Entrega repetible:** migraciones, estáticos, reinicio, persistencia, copia/restauración aislada, sesiones, permisos, CSRF, secretos y errores se verifican en el entorno elegido. Un timeout se trata como resultado desconocido hasta consultar el estado; no como permiso para repetir un pago.
8. **Cierre honesto:** no hay defectos abiertos dentro del recorrido seleccionado. Se registran todas las ejecuciones fallidas; no se borra una regresión roja ni se reduce el denominador para conseguir 100 %. Aprobación de un sublote y aprobación integral son estados distintos.

## Decisiones ya tomadas y hechos aún necesarios

| Tema | Decisión / estado |
|---|---|
| Modalidad de exposición | Internet obligatorio; local sirve para desarrollo y pruebas previas |
| Dominio y alojamiento | No contratados; URL del proveedor admisible. Selección técnica pendiente en 15, sin inferir suscripción ni gasto |
| Yape | Cuenta Yape propia autorizada y cero comisión de cobro. La viabilidad del puente se decide en el dispositivo. Ver [ensayo, umbral de decisión y límites](PAGOS_YAPE_Y_MIXTOS.md). |
| Pruebas monetarias | El usuario eligió transferencias reales de importe pequeño. Las ejecutan manualmente las personas autorizadas; fijar importe/destinatario antes de cada movimiento. Las pruebas automáticas de errores/concurrencia usan datos simulados aislados |
| QR disponible | Existe una imagen en `qr-minimarket/`. Su existencia no acredita titularidad, cuenta receptora, funcionamiento ni integración. Verificar esos hechos con el responsable antes de publicarla o pagar |
| Referencia de Yape | Registrar identidad externa solo si la fuente la proporciona. Separar ID propio del aviso, código de tres dígitos, movimiento del receptor e ID del pedido. Probar colisiones, reenvíos entre turnos y aviso tardío sin reasignación. |
| Anulación/devolución | Venta anulada, dinero devuelto y stock recibido son hechos separados. Por instrucción del usuario NO hacer nuevos yapeos para reintegrar. Política de devolución delegada sin dueño presente: pendiente de definir medio permitido, permisos, condiciones y control de abuso; la respuesta del usuario rechazó dependencia del dueño, no autorizó una salida automática de efectivo |
| Gestión de empleados | Mantener etapas 01 y 02; el cierre 01-K no aprueba02 ni la publicación pública |
| Constancia para la exposición | Mantener el caso de 100 gaseosas Inca Kola de 3 L y recuperación dos meses después. Exhibir únicamente constancias internas sin efecto tributario. Trazar presentación e historial a 12 y alcance a 16. |

## Personal no confiable y rapidez de atención

El vendedor atiende y consulta sus ventas del turno abierto. Solo ADMIN configura el receptor. El teléfono receptor permanece fuera del control del vendedor. La capa de desafío requiere probar que el cliente puede aportar evidencia vinculada a su pedido sin revelar al vendedor los códigos esperados. La consulta excepcional requiere autorización y fuente independiente. Evaluar intento por URL directa, cambios de actor, pérdida de permiso y recuperación.

Medir los cinco tramos por separado, con red, versión, volumen y muestra. Un percentil del servidor solo describe esa parte del recorrido. El corte previo propuso p95 ≤ 2 s para acciones ordinarias del servidor; verificar alcance y meta antes de aceptarla.


## Secuencia de trabajo y entregables

- **Preparación documental realizada:** se corrigieron los 18 prompts y se actualizaron objetivo y planificación de pagos; esto no ejecuta 18 auditorías.
- **00, inventario estático realizado:** se fijaron versión/build y mapa de criterios afectados. Se conserva01-K local y sus límites; no se ejecutaron criterios funcionales nuevos.
- **Ahora,02 y módulos funcionales:** continuar desde `02-DEMO-TRAZABILIDAD-01`; implementar solo los requisitos aceptados y revalidar dependencias. Los fallos detectados en01-K sobre orden temporal, FEFO y orden del borrador se conservan para 09/10/12/14.
- **09–12:** desarrollar y probar el modelo de pagos, QR, mixtos, cancelaciones, reintegros y desglose conforme 08. Verificar referencia real del abono antes de activar Yape real; sin ello, mantener bloqueada la entrega de esa capacidad.
- **13–14:** conciliar indicadores y recorridos entre roles; ejecutar los escenarios de [pagos](PAGOS_YAPE_Y_MIXTOS.md).
- **15–16:** publicar la versión candidata, comprobar URL externa y persistencia; resolver alcance tributario sin inventar obligaciones comerciales ajenas a la exposición.
- **17:** ejecutar el guion público completo contra versión congelada y evidencias; preparar segunda pasada según continuidad. No cerrar por tener un índice de pruebas ni por documentación generada.

Cada sesión termina con cambios, pruebas ejecutadas, fallos, límites y cursor. Si hay bloqueo externo, continuar tareas independientes y registrar el hecho faltante; no pedir reiteradamente autorizaciones ya concedidas ni rellenar desconocidos con suposiciones.
