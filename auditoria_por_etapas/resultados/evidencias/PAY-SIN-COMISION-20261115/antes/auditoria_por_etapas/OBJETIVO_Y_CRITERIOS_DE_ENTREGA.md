# Objetivo común de la entrega académica por internet

**Vigente: 15/11/2026, decisión DEMO-INTERNET.** La última instrucción del responsable sustituye la condición de demostración exclusivamente local de 01-K. Continúa siendo un proyecto universitario; el profesor representa al dueño de un minimarket. No existe una empresa contratante ni se exige comprar un dominio o constituir una empresa para exponer.

**Objetivo general:** entregar y demostrar un sistema de minimarket accesible mediante una URL pública HTTPS, con cuentas de administrador, almacenero y vendedor, que permita recorrer inventario → preparación → cobro en efectivo, Yape por QR o ambos → constancia e historial → control de caja y devoluciones, conservando dinero, stock y trazabilidad; cada comportamiento visible debe estar especificado en HU, CA y CP, y probado en el mismo build publicado.

La fuente funcional sigue siendo [08](../08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA). Este documento coordina el trabajo y no constituye una segunda especificación. El estado actual es **OBJETIVO ACEPTADO, ENTREGA NO VERIFICADA**. Una URL pública sin recorridos comprobados no es entrega aprobada; las pruebas locales tampoco son pruebas de publicación.

## Condiciones comprobables de terminación

1. **Acceso real por internet:** el profesor abre una URL HTTPS desde un equipo o red distintos al del desarrollador. La aplicación funciona sin depender de `localhost` ni de que esté encendido el servidor de desarrollo del estudiante. Se admite subdominio del proveedor; no se exige dominio de pago. Elegir servicio compatible con Django, almacenamiento persistente y base de datos, verificando las condiciones vigentes del plan gratuito o presupuesto antes de publicar.
2. **Recorrido de negocio completo:** abrir turno, consultar/recibir existencias, preparar venta, cobrar por los tres modos, recuperar constancia, consultar desglose y cerrar/conciliar. Inventario, ventas y dinero coinciden. Probar también rechazos y acciones de los otros roles.
3. **Yape comprobado honestamente:** QR del receptor autorizado; el abono se comprueba en un canal legítimo de la cuenta receptora mediante consulta delegada con permisos limitados o integración verificable. El dueño no debe aprobar cada venta. Una declaración interna del cajero no equivale a confirmación bancaria. Captura, sonido, QR escaneado o código escrito por el cliente no confirman por sí solos el pago. Identificar en pantalla la comprobación manual, con su literal especificado en08 antes de implementarlo; no anunciar verificación por Yape sin integración verificable. No utilizar scraping, lectura de notificaciones ni credenciales de banca como sustituto improvisado de una API.
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
| Yape | Operación delegada sin dueño presente. Alternativa recomendada a evaluar: consulta de abonos con Yape Empresa/Ayudantes, sin facultad de transferir fondos. Tiene costo y requiere confirmar disponibilidad. No acredita API ni impide una declaración falsa del empleado; el mecanismo y riesgo residual siguen pendientes de aceptación |
| Pruebas monetarias | El usuario eligió transferencias reales de importe pequeño. Las ejecutan manualmente las personas autorizadas; fijar importe/destinatario antes de cada movimiento. Las pruebas automáticas de errores/concurrencia usan datos simulados aislados |
| QR disponible | Existe una imagen en `qr-minimarket/`. Su existencia no acredita titularidad, cuenta receptora, funcionamiento ni integración. Verificar esos hechos con el responsable antes de publicarla o pagar |
| Referencia de Yape | Verificar qué identificador inequívoco muestra la app receptora usada. El código de seguridad de 3 dígitos no es una clave única global. Si no se puede identificar de manera inequívoca el abono, mantenerlo en revisión; no inventar un número de operación |
| Anulación/devolución | Venta anulada, dinero devuelto y stock recibido son hechos separados. Por instrucción del usuario NO hacer nuevos yapeos para reintegrar. Política de devolución delegada sin dueño presente: pendiente de definir medio permitido, permisos, condiciones y control de abuso; la respuesta del usuario rechazó dependencia del dueño, no autorizó una salida automática de efectivo |
| Gestión de empleados | Mantener etapas 01 y 02; el cierre 01-K no aprueba02 ni la publicación pública |
| Factura solicitada por profesor | Conservar caso de 100 gaseosas Inca Kola de 3 L y recuperación 2 meses después. Resolver trazabilidad y diferencia constancia/factura en 12/16; no afirmar emisión SUNAT sin integración |

## Personal no confiable y rapidez de atención

El cajero puede preparar cobros de su turno; no modificar receptor/QR, precios, pagos ajenos o evidencia ya registrada. No debe recibir las claves de la cuenta bancaria del negocio ni depender del dueño para cada venta. La consulta delegada oficial puede evitar acceso a fondos, pero no convierte nuestra aplicación en validador bancario ni impide por sí sola una declaración falsa interna. Se requiere una decisión explícita sobre el mecanismo y el riesgo residual. Una aprobación externa, cuando exista, debe ligarse a pedido, importe y versión; un cambio los invalida. Probar servidor/servicio, URL directa, POST alterado, sesiones antiguas y carreras de desactivación.

La rapidez se consigue evitando doble digitación y pasos innecesarios; no suprimiendo comprobación de fondos. Medir captura, servidor, tiempo bancario y espera externa por separado. Propuesta técnica inicial: p95 de acciones ordinarias del servidor <=2s tras calentamiento, con volumen/red/muestra explícitos; validar la meta antes de aceptación. No prometer tiempo bancario/humano fijo ni aprobarla con pruebas locales. La alternativa de aprobación del dueño por cada venta fue descartada por el usuario.


## Secuencia de trabajo y entregables

- **Preparación documental realizada:** se corrigieron los 18 prompts y se actualizaron objetivo y planificación de pagos; esto no ejecuta 18 auditorías.
- **00, inventario estático realizado:** se fijaron versión/build y mapa de criterios afectados. Se conserva01-K local y sus límites; no se ejecutaron criterios funcionales nuevos.
- **Ahora,02 y módulos funcionales:** continuar desde `02-DEMO-TRAZABILIDAD-01`; implementar solo los requisitos aceptados y revalidar dependencias. Los fallos detectados en01-K sobre orden temporal, FEFO y orden del borrador se conservan para 09/10/12/14.
- **09–12:** desarrollar y probar el modelo de pagos, QR, mixtos, cancelaciones, reintegros y desglose conforme 08. Verificar referencia real del abono antes de activar Yape real; sin ello, mantener bloqueada la entrega de esa capacidad.
- **13–14:** conciliar indicadores y recorridos entre roles; ejecutar los escenarios de [pagos](PAGOS_YAPE_Y_MIXTOS.md).
- **15–16:** publicar la versión candidata, comprobar URL externa y persistencia; resolver alcance tributario sin inventar obligaciones comerciales ajenas a la exposición.
- **17:** ejecutar el guion público completo contra versión congelada y evidencias; preparar segunda pasada según continuidad. No cerrar por tener un índice de pruebas ni por documentación generada.

Cada sesión termina con cambios, pruebas ejecutadas, fallos, límites y cursor. Si hay bloqueo externo, continuar tareas independientes y registrar el hecho faltante; no pedir reiteradamente autorizaciones ya concedidas ni rellenar desconocidos con suposiciones.
