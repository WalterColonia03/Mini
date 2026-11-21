# Guía de auditoría de Yape, pagos mixtos y devoluciones

**15/11/2026.** Es un guion de auditoría y análisis de riesgos; los requisitos vigentes están en 08, HU-VEN-07/10, HU-VEN-06a/b/c, RN-02/08/09 y CT-ENTREGA-ACADEMICA. Los casos de esta guía están **DISEÑADOS / NO EJECUTADOS** en la aplicación. Las cantidades grandes son fixtures; no son instrucciones de transferir dinero real.

## Lo comprobado en esta revisión

`sales/models.py` representa venta con `cash_received` y `change_given`; `checkout_sale` comprueba efectivo frente al total; `sales_receipt.html` escribe «Efectivo». No hay rutas de cobro Yape, devolución ni anulación publicadas en `sales/urls.py`. La carpeta `qr-minimarket/` contiene una imagen JPG; una imagen no demuestra integración. Los CP históricos de Yape/anulación eran futuros. Por tanto, **no afirmar que Yape, mixtos ni devoluciones ya funcionan**. Este corte es documental y de inspección, no prueba funcional ni publicación.

## Modalidad y límites de la comprobación

Se requiere QR y comprobación desde una fuente legítima de la cuenta receptora del negocio, sin aprobación personal del dueño en cada venta. El usuario requiere cero comisión de cobro: Yape Empresa/Ayudantes queda descartado. QR Yape común/Plin son candidatos de recepción; consulta delegada, referencia y aceptación del riesgo residual siguen pendientes. Ver [decisión y fuentes](resultados/DECISION-PAGOS-SIN-COMISION.md). El operador debe contrastar importe, destinatario, movimiento y referencia, asociándolo al pedido correcto. Si el operador hace el cotejo, se registra como comprobación humana; no como validación automática por banco. El cliente puede escanear y transferir, pero su pantalla no acredita el abono. Si el receptor no puede comprobarlo, se mantiene pendiente y no se entregan productos bajo una venta marcada pagada. Dos personas o dos pedidos por el mismo importe no se distinguen solo por el importe.

No se almacenan claves de la cuenta receptora ni se da acceso bancario al cajero. El QR/receptor se configura por ADMIN y se conserva su versión por solicitud. El código de seguridad de 3 dígitos sirve como cotejo adicional cuando está disponible; **no** usarlo como número de operación globalmente único ni como contraseña bancaria. No inventar longitud/formato del número de operación: primero observar la cuenta/app utilizada, documentar la fuente y fijar HU/CA/CP. No introducir PIN, clave, OTP de banca ni acceso al teléfono del cliente en el sistema. No asociar automáticamente notificaciones o capturas a ventas.

Comprobar un abono real es distinto de poder hacerlo automáticamente. Sin una integración documentada con el proveedor, el sistema solo puede registrar la comprobación humana desde un canal legítimo del receptor y evitar reutilizar la misma referencia registrada; una referencia distinta inventada por una persona no se vuelve auténtica por pasar una validación de texto. Registrar responsable y fecha, limitar permisos y conciliar movimientos ayuda a detectar ese riesgo residual.

## Estados y dinero que deben distinguirse

Modelo propuesto para implementación trazable a08: un pedido puede tener varios intentos y varios abonos. El intento puede estar pendiente/cancelado/fallido; un abono realmente recibido no desaparece por cancelar el intento. La aplicación del abono a una venta y su devolución son registros vinculados, con límites e idempotencia propios. Evitar agregar solo un campo `medio=mixto` sin importes por componente.

Para total T, Yape aplicado Y y efectivo aplicado E: `E + Y = T`. Si el cliente entrega efectivo R, `vuelto = R - E`, con `R >= E`. Ejemplo: total 30, Yape 20 y billete 20 → efectivo aplicado 10, vuelto 10; gaveta +10, Yape +20, venta 30. El exceso digital no se convierte automáticamente en vuelto de gaveta: se conserva como importe no aplicado/devolución por resolver. Por política expresa del usuario se prohíbe devolver mediante un nuevo yapeo. Está pendiente definir una política de reintegro delegada que no dependa del dueño, su medio permitido y controles; hasta entonces no diseñar un botón que prometa ejecutar el reintegro. Devoluciones acumuladas nunca superan lo recibido/aplicado pertinente; separar devolución de exceso y reintegro de venta para no contarlos dos veces.

Los siguientes nombres de estados son diseño a concretar con los textos exactos de 08 antes de escribir UI: pago pendiente, verificado manualmente, aplicado, abono sin aplicar, devolución pendiente, devolución confirmada y caso en revisión. No muestran una garantía bancaria ni equivalen a una factura fiscal.

## Matriz de escenarios a ejecutar

Cada fila exige comprobar UI, servidor, persistencia y efecto visto por el siguiente rol. Guardar antes/después de venta, pagos, devoluciones, caja, stock y eventos. Vincular cada variante a un CP escrito antes de implementarla; las filas no se cuentan aprobadas por existir.

| Escenario | Comprobación / resultado esperado | Responsable |
|---|---|---|
|01 Efectivo exacto/excedente/insuficiente | Mantener contrato y vuelto; insuficiente no confirma |11, CP-HU-VEN-01c-001 |
|02 Yape exacto por QR | Receptor y abono verificados; venta una vez; gaveta sin incremento |11, CP-HU-VEN-07-001 |
|03 Mixto 30=10+20, billete 20 | Vuelto10; separación 10/20, total 30 |09/11, CP-HU-VEN-10-001 |
|04 Importes 0, negativos, más de 2 decimales, texto/NaN | Rechazo en servidor sin mutación ni ajuste silencioso |11, CP-HU-VEN-10-001 |
|05 Yape parcial y saldo en efectivo | No venta pagada hasta completar y verificar los componentes |11, CP-HU-VEN-10-001 |
|06 Dos abonos para una venta | Registrar ambos sin reemplazar el primero; suma y referencias comprobadas |11, CP-HU-VEN-10-001 |
|07 Dos clientes pagan igual casi simultáneamente | No asociar por monto; pedido/referencia/receptor distinguen abonos |11/14, CP-ACA-003 |
|08 Un pagador distinto del comprador | No confundir nombre con prueba de pertenencia; confirmar vínculo con pedido |11/14, ampliar CP-ACA-003 antes de implementar esta variante |
|09 Captura falsa, vieja o de otra cuenta | No confirmar por la captura; comprobar movimientos receptor |11/14, CP-HU-VEN-07-002 |
|10 QR incorrecto/sustituido/ilegible | No habilitar cobro con receptor no confirmado; mantener pedido |11/15, CP-HU-VEN-07-002 |
|11 Misma referencia dos ventas, pestañas o vendedores | Un único uso permitido incluso en carrera; segunda solicitud rechazada sin mutaciones |11/14/15, CP-ACA-003 |
|12 Mismo código corto en dos pagos legítimos | No deduplicar globalmente por 3 dígitos; exigir identificación inequívoca |11, CP-HU-VEN-07-002 |
|13 Reenviar/recargar/atrás después de confirmar | Recuperar resultado; no nuevo pago/venta/stock/constancia |11/12/14, CP-ACA-003 |
|14 Timeout después del commit | Consultar estado; no repetir transferencia automáticamente |11/15, CP-ACA-003 |
|15 Pago demorado o receptor sin conexión | Pendiente; comprobar recepción antes de confirmar |11, CP-HU-VEN-07-002 |
|16 Cancelar antes de recibir dinero | Cancelar intento; cero venta, stock o devolución ficticia |10/11, CP-ACA-004 |
|17 Cancelar después del primer abono | Conservar abono, no declarar dinero devuelto; registrar resolución |11/12, CP-ACA-004 |
|18 Abono llega tras cancelación/cambio de medio | Registrar incidencia/abono sin aplicar; no cobrar dos veces |11/14, CP-ACA-004 |
|19 Exceso, duplicado o envío a destinatario equivocado | No alterar total ni inventar ingreso; exceso/duplicado recibido queda por resolver |11/12, CP-ACA-004 |
|20 Stock/precio cambia después del abono | Conservar dinero recibido; no descuento parcial; resolver saldo/devolución y nueva aceptación |10/11/14, CP-ACA-003 |
|21 Anular venta de efectivo | Permiso delegado según política a conciliar con HU06a histórica; motivo, devolución física confirmada y movimiento único |09/12, CP-HU-VEN-06a-001 |
|22 Anular Yape | Registro administrativo no revierte transferencia; reintegro separado según política pendiente, sin nuevo yapeo |12, CP-HU-VEN-06b-001 + CP-ACA-004 (refinamiento) |
|23 Anular mixto | Conservar componentes de origen; medio de reintegro sujeto a política explícita; jamás mover gaveta automáticamente ni emitir nuevo yapeo |09/12, CP-HU-VEN-06b-001 + CP-ACA-004 (refinamiento) |
|24 Reembolso parcial/segundo reembolso | Límites acumulados y vínculo al original; no reintegrar más de lo recibido; reglas parciales requieren ficha propia antes de habilitar UI |12, CT-ENTREGA-ACADEMICA/C-04; refinamiento pendiente |
|25 Reintento/timeout de devolución | No repetir el reintegro por no recibir respuesta; recuperar estado, revisar y conciliar |12/15, CP-HU-VEN-06b-001 + CP-ACA-004 (refinamiento) |
|26 Reclamo tras cerrar turno | No reescribir cierre; registrar caso administrativo pendiente |09/12, CP-ACA-004 |
|27 Producto devuelto vencido/abierto o varios lotes | Nunca volver a vender vencido; no duplicar stock; origen y disposición documentados |07/08/12, CP-HU-VEN-06c-001 |
|28 Solicitar, autorizar y ejecutar un reintegro; cambiar el QR | Distinguir los cuatro permisos. Rechazar en servidor solo las acciones sin el permiso acordado, sin mutaciones. La política pendiente no autoriza a prohibir toda solicitud ni a exigir al dueño por cada reintegro |02/14/15, CP-ACA-003 + CP-ACA-004 (refinamiento) |
|29 Cierre, historial y tablero | Bruto, anulado, reintegrado y pendiente separados; suma componentes igual total, Yape fuera de gaveta |09/12/13, CP-ACA-002 + CP-HU-VEN-10-001; reintegros sujetos a CP-ACA-004 y su refinamiento |
|30 Reinicio del alojamiento | Persisten ventas, abonos y asociaciones; no volver a utilizar referencia por pérdida de BD |15, CP-ACA-001 |

Los IDs de CP remiten a los casos escritos de 08. Las variantes con política pendiente requieren refinamiento adicional antes de implementarse; no se afirma que los casos históricos ya cubran esa ampliación. Estas filas definen cobertura a preparar, no 30 casos ejecutados ni aprobación de todos los supuestos. El alcance inicial conserva una caja: dos clientes/pestañas y solicitudes competidoras deben probarse sin inventar múltiples cajas comerciales.

## Pruebas de abuso interno y atención rápida

Añadir a 14/15: cajero modifica importe tras comprobación; usa referencia ajena; repite aprobación; intenta cambiar QR; otro cajero intenta cobrar el pedido; trabajador desactivado con pantalla abierta; autoaprobación con petición alterada; administrador delegado cambiaQR con un cobro pendiente; retiro/devolución sin permiso; eliminación o edición de movimientos; anulación falsa sin recibir mercadería; dos devoluciones concurrentes; descuento/precio manipulado. Exigir rechazo en servidor y ausencia de efectos, no solo ocultar botones. Alertas o funciones de revisión nuevas requieren sus HU/CA/CP antes de mostrarse.

Para rapidez: medir navegación por teclado, búsqueda, escaneo si existe lector, edición de cantidades, selección de medio, preparación de solicitud Yape, comprobación por canal delegado, confirmación y entrega de constancia. Registrar mediana/p95 del sistema y espera humana/bancaria aparte, número de acciones y errores; ensayar clientes sucesivos y solicitudes simultáneas respetando la caja única. No publicar una cifra de atención garantizada ni convertir el QR estático en comprobación de abono. No introducir una cola de autorizaciones que dependa del dueño para toda venta; cualquier cola operativa aceptada debe trazarse a su HU; no habilitar múltiples borradores incompatibles con la regla vigente sin refinamiento expreso.

## Investigación anterior y decisión de costo posterior

La propuesta de aprobación obligatoria del dueño por cada venta fue rechazada por el usuario. Yape publica una alternativa distinta: **Ayudantes de Yape Empresa** consultan ventas del día sin poder yapear ni ver saldo; esto separa consulta y acceso al dinero. Los requisitos publicados de Yape Empresa contemplan Credimás o registro con DNI y cuenta Yape; no se descarta por no contar con RUC, pero la cuenta concreta debe comprobar elegibilidad. El costo publicado es 2,95 % sobre ventas diarias recibidas por QR/contacto/nuevo número. El usuario descartó esta alternativa por costo; no se realizó afiliación.

**Límite:** es una consulta oficial para la persona, no una API de confirmación en nuestro sistema. Un empleado podría mentir al registrar el resultado, reutilizar datos con otra referencia o coludirse; deduplicación, permisos, registro de actor y conciliación permiten controlar/detectar parte del riesgo, no impedirlo absolutamente. Para confirmación automática independiente se necesita un canal autenticado del proveedor disponible y permitido; no se ha encontrado ni probado uno gratuito que satisfaga todas las restricciones. No crear un lector de notificaciones o pantallas como supuesto equivalente bancario.

| Alternativa | Beneficio | Costo / riesgo / decisión |
|---|---|---|
| Ayudantes Yape, cotejo humano delegado | Dueño ausente; empleado consulta abonos sin transferir fondos | DESCARTADA por la exigencia de cero comisión; se conserva como antecedente, no recomendación vigente |
| QR Yape común o Plin interoperable | Recepción sin comisión en la modalidad publicada; pagador puede usar Yape | CANDIDATO de recepción. No se verificó consulta delegada/API gratuita ni cuenta del usuario; no dar credenciales al cajero |
| Integración oficial con proveedor | Confirmación técnica independiente y recuperación de estado | Afiliación/credenciales/costos/elegibilidad por comprobar; flujoQR específico debe verificarse. NO DISPONIBLE en proyecto |
| QR personal y cajero con acceso pleno | No requiere integración | Expone dinero/claves o depende del dueño; DESCARTADA para atender la necesidad actual |
| Simulación claramente identificada | Prueba estados sin dinero | No cumple por sí sola la transferencia real elegida; útil solo para casos automáticos aislados |

**Reintegros sin nuevo yapeo:** aún falta acordar el medio. Como propuesta de menor alcance, permitir salida en efectivo solo bajo reglas explícitas de permiso delegado, abono previamente verificado, venta/reclamo vinculado, importe acumulado no mayor al adeudado, comprobación de stock devuelto cuando corresponda, movimiento de caja y conciliación. No fijar topes arbitrarios ni otorgar permiso al cajero por silencio. Si no hay evidencia del abono o saldo suficiente, mantener pendiente; no prometer devolución inmediata ni negar derechos de reclamación.

## Fuentes oficiales consultadas el 15/11/2026

- [Yape: cobrar utilizando QR](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/30--donde-encuentro-mi-qr): describe compartir el QR para recibir dinero. No acredita confirmación automática por nuestra aplicación.
- [Yape: identificar un yapeo falso](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/como-identifico-un-yapeo-falso): comprobar el movimiento/saldo desde el receptor; una pantalla del emisor puede ser falsa.
- [Yape: código de seguridad](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/como-puedo-yapear-a-alguien-que-no-esta-en-mis-contactos): describe 3 dígitos. La conclusión de no usarlo como identificador global es de diseño: un espacio tan pequeño permite repeticiones.
- [Yape: cancelar un pago equivocado](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/puedo-cancelar-un-pago-si-me-equivoque-de-contacto-o-monto-a-yapear) y [devolver un abono](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/parece-que-alguien-me-ha-yapeado-por-error-puedo-devolver-el-yapeo): no se promete reversión unilateral; la ayuda describe un nuevo envío como mecanismo posible. Ese mecanismo NO está permitido en este proyecto por instrucción del usuario; citar la fuente no lo autoriza.
- [Yape: integración de comercio por internet](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/como-puedo-tener-la-opcion-de-compras-por-internet-codigo-de-aprobacion-yape-en-l): remite a pasarelas. No se infiere API gratuita, acceso sin afiliación ni que ese flujo seaQR.
- [Culqi: cargos Yape](https://docs.culqi.com/es/documentacion/pagos-online/cargo-unico/tokens-yape) y [pruebas](https://docs.culqi.com/es/documentacion/pagos-online/tarjetas-de-prueba): alternativa documentada de integración, no contratada ni seleccionada para este proyecto; comprobar requisitos de afiliación si cambia el contexto.

No se fijan comisiones, límites bancarios ni disponibilidad de planes con información supuesta. No se realizó ninguna transferencia ni se comprobó la titularidad del QR en esta revisión.

- [Yape: acceso a Empresa](https://www.yape.com.pe/preguntas-frecuentes/yape-empresa/como-puedo-acceder-a-yape-empresa), [permisos de Ayudantes](https://www.yape.com.pe/preguntas-frecuentes/yape-empresa/que-podran-hacer-mis-ayudantes) y [costo](https://www.yape.com.pe/preguntas-frecuentes/yape-empresa/yape-empresa-tiene-algun-costo): fundamento histórico de la alternativa descartada por costo. Condiciones consultadas 15/11/2026; no hay afiliación propuesta vigente.
