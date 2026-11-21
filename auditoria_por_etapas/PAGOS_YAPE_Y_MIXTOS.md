# Guía de cobro y conciliación de Yape para las auditorías

**Corte documental del 20/11/2026.** Aplicar junto con [HU-VEN-07](../08_Historias_de_Usuario.md#HU-VEN-07), [HU-VEN-10](../08_Historias_de_Usuario.md#HU-VEN-10) y [el contrato académico](../08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA). Las filas de prueba son trabajo por ejecutar.

## Decisiones y alcance

**ACEPTADO por el responsable en el brief del 17/11:** efectivo, digital y mixto, varios abonos, QR estático Yape de la cuenta propia autorizada, cero comisión de cobro, tres roles, cuenta sin RUC ni identidad de familiares, constancia interna, demostración real con importes pequeños sobre HTTPS público y atención ordinaria sin aprobación del dueño. Quedan prohibidos los nuevos yapeos para devolver. Costear teléfono, conectividad, alojamiento y mantenimiento por separado. Se seleccionó la dirección de comprobación por capas. El pagador introduce el importe en su billetera. El QR identifica al receptor y puede seguir circulando después de cancelar el pedido.

**PROPUESTO:** puente propio en Android, transporte autenticado, captura del desafío por el cliente, recuperación, asociación y pantallas de revisión. El proyecto aún debe demostrar cada capa. Las pasarelas Izipay y Mercado Pago y Yape Empresa/Ayudantes quedan fuera de la ruta actual. Las comparaciones y los informes de traspaso de noviembre son antecedentes. Se excluyen el reenvío indiscriminado por apps de terceros, el ajuste artificial del precio y la asignación por monto.

**DECISIÓN PENDIENTE:** manejo de Plin, habilitación excepcional de cotejo manual, quién puede autorizar devoluciones sin el dueño, medio y beneficiario, límites y plazos. Los topes S/15–15–30 y las propuestas R2/M2 previas carecen de aprobación operativa. La falta de sencillo o de delegado mantiene visible la obligación. Registrar manualmente un incidente sigue permitido como diseño de revisión, con efectos financieros bloqueados hasta contar con una política aceptada y evidencia independiente del solicitante.

## Encaje en el producto

El checkout de Django trabaja hoy con efectivo y lotes en `r1-pmv/sales/services.py`. `discard_active_draft` descarta líneas y `checkout_sale` revalida carrito y stock. Antes de admitir dinero, el pedido debe conservar identidad, versión y evidencia incluso si falla esa confirmación. `cash/services.py` calcula hoy apertura más ventas. En un mixto de S/15 con Yape S/10 y billete S/10 con vuelto S/5, el esperado de gaveta aumenta S/5. Registrar entradas y salidas físicas o su neto una sola vez. Un movimiento QR tiene efecto cero en la gaveta.

Caja única y borrador activo según el corte. Dos pedidos sucesivos y dos pestañas sí son casos de prueba. Dos cajas simultáneas son una dependencia futura a mapear. ADMIN configura el receptor, controla los accesos y concilia incidencias. VENDEDOR atiende su turno, solicita cancelaciones y consulta sus ventas del turno abierto (HU-VEN-05a). ALMACENERO gestiona existencias y puede calificar el destino físico según HU-VEN-06c en su alcance futuro. La firma de un reintegro requiere competencia financiera distinta. Revisar exposición del QR al girar el monitor y acceso a otros clientes o a los avisos del receptor.

## Capas y criterio para acreditar

1. **Origen y custodia.** Comprobar la app emisora y procedencia de instalación en el equipo receptor autorizado. Un nombre, icono o sonido es insuficiente. Separar acceso al equipo y al secreto del puente del acceso de VENDEDOR. El control o compromiso de ese teléfono permite fabricar evidencia aparente.
2. **Transporte.** Autenticar el dispositivo, proteger el tránsito con TLS y comprobar integridad, revocación y reintentos sin pérdida. Un mensaje autenticado representa lo observado por ese equipo. Conservar evidencia mínima y sanitizada. Restringir la observación a Yape y al uso autorizado. Excluir OTP, secretos, contenidos de otras apps y automatización bancaria por accesibilidad.
3. **Recepción del dinero.** Distinguir aviso local, movimiento real del receptor y crédito comprobado. Comparar en ensayo con los movimientos del titular. La clave local de Android puede cambiar o identificar una actualización. Un segundo aviso puede repetir el primero o representar otro abono legítimo.
4. **Vínculo con pedido.** Propuesta: abrir primero una sesión de cobro con ID propio y receptor versionado. El cliente aporta, desde su confirmación, el código sin que el cajero vea los códigos esperados del receptor. Evaluar una vía de entrada vinculada a ese pedido y separada de los permisos del cajero, consumo único y límites de intentos. Nunca pedir PIN o clave de Yape. Nota opcional y hora solo refuerzan contexto. Examinar otro cliente, tercero, cancelación y pago tardío incluso cuando hay un único candidato visible. El aviso no incluye por definición el ID del pedido. Si los hechos observables son compatibles con asignaciones distintas, conservar pendiente. El código de tres dígitos del pago tampoco demuestra por sí solo presencia, exclusividad ni ausencia de colusión.
5. **Aplicación única.** Distinguir repetición de transporte, repetición del aviso y doble uso del mismo crédito en otra venta, incluso entre turnos. Aplicar bajo transacción y recuperar el mismo resultado ante reintento. Si el canal carece de identidad suficiente para distinguir dos operaciones, aislar la ambigüedad y conservar ambas observaciones.
6. **Conservación.** Registrar intento, aviso, crédito, aplicación, venta y obligación/entrega con estados separados. Una venta se confirma una vez cuando efectivo neto aplicado + digital aplicado = total. Abono menor deja saldo, excedente queda sin aplicar o por devolver. Un aviso huérfano jamás acredita la compra siguiente. Solo reconstruir un vínculo anterior con evidencia suficiente. Si falla la confirmación técnica con dinero recibido, recuperar el mismo pedido sin volver a cobrar ni descontar stock dos veces.

**Salida visible ante duda**, a especificar con literales y CP antes de implementar: pagado comprobado, pendiente de comprobar, saldo y caso en revisión. Mantener el pedido y permitir continuar la atención de acuerdo con la regla de borrador único, preservando la incidencia antes de liberar el puesto. Nada de entrega como pagada ni segundo cobro sobre saldo desconocido. Si ADMIN habilitara cotejo humano por excepción, exigir movimiento del receptor, asociación, actor distinto de la sola declaración del cajero, motivo y conciliación posterior. Un bypass manual que apruebe una captura incumple RN-02.

## Ensayo decisivo en el receptor — pendiente de cuenta y dispositivo

Preparar Galaxy A52s 5G con Android 14/One UI 6.1 declarado, versión de Yape, cuenta y QR autorizados, enlace autenticado de prueba, servidor HTTPS y pagadores voluntarios. Verificar titularidad, condiciones de uso, permiso del titular, minimización y cero comisión para esa modalidad. Acordar y registrar presupuesto por operación antes del ensayo humano. Para la fase previa usar muestras sintéticas sin efectos contables reales.

| Prueba en dispositivo o variante aislada | Observar y contrastar |
|---|---|
| Un yapeo pequeño acordado (por ejemplo S/1) | En pagador, aviso y movimientos del receptor: importe, código, posibles datos de emisor, nota y referencia real si existe. Guardar esquema y evidencia anonimizada |
| Dos yapeos seguidos y dos teléfonos para un pedido | Cuántos movimientos hubo, cuántos avisos se emitieron/reemplazaron/agruparon, qué evidencia permite distinguir cada uno y a qué pedido puede aplicarse |
| Pantalla bloqueada, app cerrada, inactividad, reinicio, permiso revocado, pérdida de red | Entrega o ausencia, salud del puente, cola y reenvío. Simular respuesta perdida del servidor tras guardar. Comprobar entre turnos que no se acredita dos veces |
| Mismos atributos, códigos repetidos, cancelación de A y apertura de B | Forzar colisiones con fixtures. Comparar dos historias plausibles con iguales señales; si no se distinguen, ambas quedan en revisión. El pago tardío nunca entra en B por ser el único abierto |
| Plin, dinero sin aviso y aviso sin compra | Documentar lo que realmente aparece en esta modalidad. Sin desafío/evidencia suficiente, revisión. Controlar receptor ajeno aun si el cliente muestra captura |
| Rapidez y conciliación | Tiempos de pago en app, llegada del aviso, transporte, commit y acción humana. Anotar incertidumbre de relojes, tamaño de muestra y fallos. Comparar créditos/aplicaciones contra movimientos reales |

**Continuar con comprobación asistida por el puente** solo al demostrar uso permitido, identidad/custodia del receptor, recepción/recuperación, asociación suficiente y consumo único bajo las variantes evaluadas. Registrar el riesgo residual y el alcance aceptado de la muestra. Si falla la persistencia o se pierden los dos avisos, conservar el puente solo como apoyo a conciliación. Si falla la asociación, bloquear la acreditación automática aunque el reenvío sea perfecto. Ofrecer efectivo para un pedido nuevo o aún sin transferencia incierta. La variante manual requiere decisión y prueba propias.

Yape documenta que el pagador ingresa el monto y que el código de tres dígitos aparece en ambos extremos para pagos personales con QR. Esto orienta el ensayo. Campos accesibles al puente, persistencia, Plin y permiso para el tratamiento propuesto requieren verificación específica. [Cómo pagar con QR](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/31--como-hago-un-pago-con-qr) · [Verificación del receptor](https://www.yape.com.pe/preguntas-frecuentes/yape-negocios/como-puedo-verificar-que-he-recibido-un-pago-por-yape).

## Cancelaciones y reposición

Pedido S/10 con S/3 recibidos y cancelación → obligación S/3. Pedido vigente de S/10 con S/15 recibidos → aplicación S/10 y exceso S/5. Si se cancela por completo antes de entregar, resolver los S/15 recibidos, conservando devoluciones/reservas previas. Una nueva compra no absorbe automáticamente esa deuda. Si en una compra de S/15 entran S/15 digitales y los S/5 físicos previstos seguían pendientes, el efectivo pendiente puede quedar en cero. Si ya se recibieron S/5 en billetes, se conservan S/20 brutos y una obligación de S/5. Registrar una salida solo al entregar los billetes con autorización. Acreditar la devolución exige beneficiario, autorización, capacidad por origen y evidencia de entrega única. Tras el cierre original se conserva el acta según RN-08/RN-10. Un producto dañado se trata según HU-VEN-06c y la situación física de la mercadería.

Ejemplo propuesto para HU-CAJA-03 y CP-ACA-004: caja S/0, obligación S/10, solicitud de reposición S/20. Solicitud, aprobación o rechazo dejan la gaveta en S/0. Solo tras recepción física documentada sube a S/20. Si una devolución en efectivo está permitida y se autoriza y entrega por separado, queda S/10. Registrar fuente, actores y turno. Si se rechaza o falta dinero, persiste la deuda. Reintento, concurrencia o resultado incierto no habilitan una segunda entrega. Conciliar billetes contados, saldo esperado y obligaciones. Una solicitud de reposición de existencias corresponde a otra etapa.

## Matriz de escenarios a ejecutar

Cada fila exige comprobar UI, servidor, persistencia y efecto visto por el siguiente rol. Guardar antes/después de venta, pagos, devoluciones, caja, stock y eventos. Vincular cada variante a un CP escrito antes de implementarla; las filas no se cuentan aprobadas por existir.

| Escenario | Comprobación / resultado esperado | Responsable |
|---|---|---|
|01 Efectivo exacto/excedente/insuficiente | Mantener contrato y vuelto; insuficiente no confirma |11, CP-HU-VEN-01c-001 |
|02 Yape exacto por QR | Receptor y abono verificados; venta una vez; gaveta sin incremento |11, CP-HU-VEN-07-001 |
|03 Mixto 30=10+20, billete 20 | Vuelto10; separación 10/20, total 30 |09/11, CP-HU-VEN-10-001 |
|04 Importes 0, negativos, más de 2 decimales, texto/NaN | Rechazo en servidor sin mutación ni ajuste silencioso |11, CP-HU-VEN-10-001 |
|05 Yape parcial y saldo en efectivo | No venta pagada hasta completar y verificar los componentes |11, CP-HU-VEN-10-001 |
|06 Dos abonos de S/3 y S/7 desde dos teléfonos para una compra de S/10 | Registrar ambos sin reemplazar el primero; suma y referencias comprobadas |11, CP-HU-VEN-10-001 |
|07 Dos clientes pagan igual casi simultáneamente | No asociar por monto; pedido/referencia/receptor distinguen abonos |11/14, CP-ACA-003 |
|08 Un pagador distinto del comprador | No confundir nombre con prueba de pertenencia; confirmar vínculo con pedido |11/14, CP-ACA-003, verificar asociación del tercero antes de habilitar la variante |
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
|19 Exceso, duplicado o envío a destinatario equivocado | No alterar total ni inventar ingreso; solo una segunda transferencia real produce dinero adicional por resolver |11/12, CP-ACA-004 |
|20 Stock/precio cambia después del abono | Conservar dinero recibido; no descuento parcial; resolver saldo/devolución y nueva aceptación |10/11/14, CP-ACA-003 |
|21 Anular venta de efectivo | Permiso delegado según política a conciliar con HU06a histórica; motivo, devolución física confirmada y movimiento único |09/12, CP-HU-VEN-06a-001 |
|22 Anular Yape | Registro administrativo no revierte transferencia; reintegro separado según política pendiente, sin nuevo yapeo |12, CP-HU-VEN-06b-001 + CP-ACA-004 (refinamiento) |
|23 Anular mixto | Conservar componentes de origen; medio de reintegro sujeto a política explícita; jamás mover gaveta automáticamente ni emitir nuevo yapeo |09/12, CP-HU-VEN-06b-001 + CP-ACA-004 (refinamiento) |
|24 Reembolso parcial/segundo reembolso | Límites acumulados y vínculo al original; no reintegrar más de lo recibido; refinar CA y CP de imputación parcial antes de habilitar la interfaz |12, CT-ENTREGA-ACADEMICA/C-04; refinamiento pendiente |
|25 Reintento/timeout de devolución | No repetir el reintegro por no recibir respuesta; recuperar estado, revisar y conciliar |12/15, CP-HU-VEN-06b-001 + CP-ACA-004 (refinamiento) |
|26 Reclamo tras cerrar turno | No reescribir cierre; registrar caso administrativo pendiente |09/12, CP-ACA-004 |
|27 Producto devuelto vencido/abierto o varios lotes | Nunca volver a vender vencido; no duplicar stock; origen y disposición documentados |07/08/12, CP-HU-VEN-06c-001 |
|28 Solicitar, autorizar y ejecutar un reintegro; cambiar el QR | Distinguir los cuatro permisos. Rechazar en servidor solo las acciones sin el permiso acordado, sin mutaciones. La política pendiente no autoriza a prohibir toda solicitud ni a exigir al dueño por cada reintegro |02/14/15, CP-ACA-003 + CP-ACA-004 (refinamiento) |
|29 Cierre, historial y tablero | Bruto, anulado, reintegrado y pendiente separados; suma componentes igual total, Yape fuera de gaveta |09/12/13, CP-ACA-002 + CP-HU-VEN-10-001; reintegros sujetos a CP-ACA-004 y su refinamiento |
|30 Reinicio del alojamiento | Persisten ventas, abonos y asociaciones; no volver a utilizar referencia por pérdida de BD |15, CP-ACA-001 |

Los IDs de CP remiten a los casos escritos de 08. Las variantes con política pendiente requieren refinamiento adicional antes de implementarse; no se afirma que los casos históricos ya cubran esa ampliación. Estas filas definen cobertura a preparar, no 30 casos ejecutados ni aprobación de todos los supuestos. El alcance inicial conserva una caja: dos clientes/pestañas y solicitudes competidoras deben probarse sin inventar múltiples cajas comerciales.

