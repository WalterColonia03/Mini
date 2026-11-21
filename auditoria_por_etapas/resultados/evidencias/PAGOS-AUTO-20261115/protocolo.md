# Protocolo automático y contraste de recomendaciones · 15/11/2026

Estado: PROPUESTO. Investigación y diseño, sin implementación, cuentas, pagos ni publicación. No modifica08 ni etapas. Revisados DICTAMEN-PAGOS-ASTRA, REVISION-PROPUESTA-GEMINI-PAGOS y el nuevo texto Argón localizado en `.codex/attachments/b2743722-b7b6-4169-94e1-f840edb4f82a/Texto pegado.txt`.

## Cambio de criterio práctico

La exigencia de una segunda persona para TODOS los pagos fue una política conservadora del dictamen anterior, no una necesidad técnica demostrada. Añade trabajo y costo y no elimina colusión. Es razonable investigar y proponer confirmación automática del flujo ordinario, aparcando excepciones. No hace falta confundir automatización con garantía absoluta.

La propuesta Argón mejora la recogida de una reclamación ciega, pero vuelve a excederse al decir imposible apropiación, riesgo cero, respaldo infalible o tres segundos. No se puede aprobar una recomendación porque incluya modelos con nombres correctos. `OneToOne(ObservedPaymentEvent)` hace único el uso de esa FILA, no de una transacción bancaria que podría haber generado varias filas/eventos. `select_for_update(Sale)` y devoluciones acumuladas<=Sale.total no cubren dinero anterior a Sale, excesos, reintegros externos con resultado desconocido ni dos operaciones cuyos saldos se reservan por distintos caminos. La reserva debe hacerse sobre el origen monetario/deuda compartido y persistir durante incertidumbre.

**Nueva prioridad transmitida por el agente principal:** usuario acepta evaluar comisión, pide importe fijo en QR y cancelación sin efectivo. Esto hace preferible investigar primero un flujo con pasarela y referencia de orden, en lugar de construir dos canales y mantener Ayudante por cada compra. Sigue pendiente si QR puede abrir checkout mediante cámara o debe escanearse obligatoriamente dentro de Yape.

## 1. Principal si se admite QR que abre checkout: importe servidor y API oficial

**INFERIDO / PROPUESTO:** mostrar un QR con URL HTTPS opaca de un intento, que el comprador abre con la cámara del teléfono. La página muestra negocio/receptor, pedido y monto fijado por servidor. El comprador ingresa SU número Yape y SU código de aprobación en su propio teléfono mediante el formulario de integración oficial; el cajero no lo recibe ni lo dicta, y el sistema no lo registra en logs, analítica o evidencia. El QR conduce al pago; no se presenta como QR nativo Yape/Plin ni como pago escaneado dentro de Yape.

**VERIFICADO DOCUMENTALMENTE:** la guía Mercado Pago Perú Checkout API vía Orders documenta formulario de celular/OTP, generación de token, creación con `external_reference`, `total_amount`, `X-Idempotency-Key` y respuesta de procesamiento; tras acreditación se utiliza reembolso, mientras una orden manual no procesada puede cancelarse. La guía recomienda notificaciones para actualizaciones posteriores. [Guía Yape Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-api-orders/payment-integration/websites/yape?scope=prod).

Este diseño no demuestra elegibilidad de una cuenta DNI para producción. Registro personal, credenciales visibles, integración Yape habilitada, cobro real y refund real son cinco comprobaciones diferentes. No cambiar toda la planificación a “resuelto” antes del ensayo de cuenta.

### Algoritmo principal concreto

1. Preparar pedido durable versionado con líneas, total aceptado, receptor comercial esperado y pendiente. Crear intento individual por cada aporte (3 y7 para pedido10). Importe/moneda/versión los calcula y almacena servidor; cliente no puede modificarlos mediante POST ni querystring. Si el cajero propone división, suma de reservas de aportes<=saldo pendiente bajo bloqueo.
2. Crear URL con token opaco de alta entropía y caducidad, sin datos personales ni acceso al resto de pedidos. La posesión del enlace permite pagar ese intento, no consultar pagos ajenos, cambiar precio/receptor o ejecutar reintegro. Pantalla muestra importe antes de consentimiento del pagador.
3. El cliente tokeniza los datos siguiendo SDK oficial. No capturar el OTP en el POS, notificaciones, capturas o accesibilidad. El backend usa token e importe almacenado para crear/procesar orden con credencial de la cuenta autorizada. Reusar el mismo intento/clave ante doble clic; no crear nueva operación por recargar.
4. Registrar provider_order_id y payment/transaction_id con unicidad por proveedor/cuenta/entorno, external_reference→intento. Al recibir respuesta o webhook, verificar autenticidad según protocolo oficial; recuperar estado autenticado de la orden cuando haga falta. Comprobar cuenta receptora/entorno, moneda, importe, estado acreditado y vínculo persistido. La página de retorno “éxito” y parámetros del navegador jamás confirman pago.
5. Persistir pago externo confirmado antes de efectos locales. Bajo locks de pedido/abonos, aplicar el dinero una vez; al completar, validar stock y confirmar Sale/stock una vez. El banco ya cobró aunque la confirmación de Sale falle: conservar CUBIERTO_PENDIENTE_CONFIRMACION y recuperar/reintegrar según política.
6. Timeout de crear/procesar: RESULTADO_DESCONOCIDO, no segundo envío ni nuevo intento automáticamente. Recuperar con identidad persistida/consulta y notificación; no asumir que un timeout significa rechazo. Si un webhook se repite/fuera de orden, el estado confirmado por proveedor y la idempotencia evitan regresión/duplicación.
7. Cancelar antes de cobro: cerrar intento y cancelar orden si estado/proveedor lo permiten. Una orden pagada tardíamente después de cancelación conserva abono y obligación de reintegro; no paga el siguiente pedido.
8. Cancelar después de cobro: reservar saldo reintegrable del payment original; refund del proveedor con identidad persistida/idempotencia documentada y consulta de estado. Nunca transferencia nueva ni selector de destino a favor del cajero. Mantener `REEMBOLSO_PENDIENTE` o `RESULTADO_DESCONOCIDO` hasta confirmación; no volver a enviarlo por no recibir respuesta.

### Qué mejora respecto al puente

- Referencia de orden creada por nosotros y confirmación autenticada del proveedor: dos clientes que pagan lo mismo quedan separados por IDs, no por código corto/nombre.
- Monto elegido en servidor; el cliente no tipea el precio ni se añaden céntimos identificadores.
- Refund vinculado al pago original evita usar efectivo y evita elegir arbitrariamente un beneficiario.
- No depende del A52s como canal crítico de recepción ni requiere personal adicional para acreditar cada compra.

### Qué NO resuelve la pasarela

- Stock puede agotarse entre iniciar y pagar. Propuesta: reserva real con expiración corta y política de precio congelado, si se acepta; o conservar abono y refund si no puede cumplirse. No asumir reserva ya implementada. No mantener transacción SQL abierta esperando comprador.
- Un token de checkout visto por dos teléfonos puede originar acciones concurrentes. El backend debe reutilizar el intento, reservar el aporte y no emitir órdenes nuevas sin límite. Si aun así se reciben dos pagos reales, el segundo queda como exceso/reintegro, no se pierde.
- Cliente y cajero pueden cambiar/cancelar compras o ocultar entrega física; refund original reduce desvío directo, pero no prueba que devolvieron mercadería ni evita sabotaje/costo de comisiones.
- La confirmación de proveedor no protege credenciales expuestas, receptor mal configurado, servidor comprometido, QR físico sustituido o uso de una cuenta no autorizada.
- Si se acepta un pago3 y otro7, son dos operaciones y posiblemente dos cargos fijos. No calcular comisión solo sobre total10 como si hubiese una transacción.
- El neto liquidado puede ser menor al bruto, y no todo saldo está disponible para refund. Un cobro10 no demuestra liquidez para devolver10. Debe comprobarse si comisión se devuelve, cuándo queda saldo disponible, retenciones y si se necesita un fondo autorizado previo.
- “Sin efectivo” no significa “instantáneo”. Deben probarse destino y plazo de devolución real de Yape en esta modalidad; la documentación genérica no prueba que vuelva inmediatamente al mismo celular.

**VERIFICADO DOCUMENTALMENTE:** Orders describe reembolsos totales/parciales; parcial identifica transacción; exige saldo disponible suficiente y contempla ventana de180 días. Su ejemplo de destino menciona otros medios, por lo que no se extrapola un plazo/destino concreto Yape. [Reembolsos y cancelaciones Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-api-orders/payment-management/refunds-cancellations).

### Puerta de aceptación principal

Antes de integrar todo el producto: confirmar elegibilidad en cuenta propia autorizada sin RUC, probar QR que abre correctamente checkout en dos teléfonos, importe inalterable en servidor, dos pagos iguales ligados a órdenes diferentes y un cobro real pequeño seguido de refund al origen. Registrar bruto/comisión/neto/disponible, devolución total/parcial, resultado perdido y plazo observado. Fallar cualquiera no se salva con sandbox ni con un “Ayudante infalible”. Si no habilita producción DNI, esta alternativa permanece bloqueada; no usar familiares.

## 2. Alternativa con QR nativo receptor y puente: automático ordinario con riesgo residual

Si se mantiene escaneo dentro de Yape y recepción directa común, puede plantearse un proceso automático sin contratar otra persona por venta. Es inferior a una referencia bancaria de orden y necesita aceptación explícita del riesgo de asociación. El cambio de política no debe fingir que resolvió ese riesgo.

**VERIFICADO DOCUMENTALMENTE:** Yape explica que notificación receptora contiene nombre/importe y un código de seguridad de tres dígitos también mostrado al pagador. [Ayuda Yape](https://www.yape.com.pe/preguntas-frecuentes/yape-negocios/como-puedo-verificar-que-he-recibido-un-pago-por-yape). Android entrega identidad de paquete/publicador y una clave del REGISTRO DE NOTIFICACIÓN; no es una referencia bancaria. [StatusBarNotification](https://developer.android.com/reference/android/service/notification/StatusBarNotification).

### Condiciones previas

Teléfono fuera de control del cajero, app oficial y versiones/firmante controlados, listener permitido y ensayado, TLS+clave individual revocable, parser conservador, historial durable, conciliación legítima posterior, permisos que impiden al cajero enumerar abonos no vinculados. No inferir capacidad en A52s Android14/OneUI6.1 solo por modelo. Revalidar tras actualización; no accesibilidad ni bypass.

### Algoritmo propuesto

1. Crear intento antes de mostrar QR, fijando pedido/version/receptor/importe/moneda. Sincronizar salud del puente. El QR estático no incorpora nuestro intento; registrar esa limitación.
2. Cliente paga y aporta el código receptor de3dígitos y nombre tal como figura; puede introducirlo en una pantalla propia o dictarlo al cajero. No es aprobación bancaria ni secreto robusto. No devolver lista de candidatos, nombres, códigos o “hay un abono porX” al POS.
3. Servidor persiste reclamación antes de revelar resultado. Cada corrección cuenta; límites por actor/dispositivo/turno y receptor/ventana, no solo por pedido que el cajero puede recrear. No aceptar selección libre entre abonos. Mensajes uniformes para no convertir la búsqueda en oráculo.
4. Al llegar observación válida, resolver revisiones/agrupaciones antes de crear un abono canónico. Aviso sin importe/moneda/semántica claros, resumen agrupado, origen no aprobado, posible reemisión o restauración incompleta → revisión, nunca saldo nuevo por UUID.
5. Formar candidatos de la cuenta/modalidad/moneda correctas, recepción individual, importe exacto, nombre normalizado conservador y código exacto, no usados/reservados/reclamados por otro pedido, dentro de ventana operacional medida. Hora solo filtro auxiliar: timestamp de publicación puede no ser hora bancaria. No matching difuso de nombres con IA para aprobar.
6. AUTOAPLICAR únicamente si hay un candidato admisible, no hay conflicto/duplicación conocida ni hueco de recuperación, reclamación consistente y presupuesto de intentos vigente. Releer condiciones bajo lock; reservar/aplicar al pedido una vez. Si suma cubre precio/stock válidos, confirmar venta una vez. Para pago3+7 se ejecuta por separado; venta solo al total.
7. Cero candidatos: continuar esperando sin mostrar evidencia ajena y sin pedir otro pago. Más de uno o coincidencia incompleta: aparcar. Evento de intento cancelado/viejo o importe excedente: no reutilizar para pedido activo; conservar y resolver. Cancelación conserva la reclamación anterior para reconocer avisos tardíos.
8. Fallo de canal: pausar nuevos QR, mantener pedidos pendientes y seguir atendiendo otras compras en efectivo si procede. Revisiones excepcionales pueden resolverse al terminar turno por personal ya existente con acceso legítimo; no requiere una persona dedicada a cada cobro. Sin un canal legítimo de resolución no se entrega mercancía ni se exige pagar nuevamente.

El requisito “un candidato admisible” es una condición necesaria de este protocolo, no prueba de pertenencia bancaria. Un abono ajeno aún no reclamado puede ser el único y compartir todos los datos; una venta dirigida por cajero coludido puede conocerlos. Ese riesgo permanece incluso sin colisión visible. No afirmar que una ventana o nombre elimina casos que no puede observar.

### Adivinación, sin falsas probabilidades

Un código de tres dígitos tiene a lo sumo1.000 valores. Solo si fuese uniforme e impredecible, con un objetivo conocido y q intentos distintos, la probabilidad de acertarlo sería q/1.000 (hasta1). Con m objetivos compatibles, una cota de unión idealizada sería min(1,q·m/1.000); no es estimación de fraude real. No está documentada aquí distribución/uniformidad del generador ni independencia entre pagos. Nombre/monto conocidos no aportan entropía secreta; código observado directamente eleva el éxito del ataque dirigido, no lo reduce a1/1.000.

Propuesta para piloto, NO política aceptada: máximo3 reclamaciones de código por intento y umbral global de fallos por actor/receptor que fuerce revisión; el segundo parámetro se fija según volumen/error medido. Los límites deben sobrevivir cancelar/recrear pedido, logout y cambio de caja. No fijar un límite tan alto que permita enumerar1.000 valores ni tan bajo que cualquier error provoque bloqueo global malicioso. Registro/alerta y suspensión específica, no prometer imposibilidad de abuso.

### Amenazas controladas y residuales

| Caso | Control / límite |
|---|---|
| Captura falsa sin abono | No existe evento receptor admisible: no aplicación |
| Cajero marca “pagó” | No endpoint que convierta declaración en abono |
| Cajero enumera pagos libres | No bandeja/lista; respuesta uniforme y límites globales |
| Mismo abono dos ventas | Canónico+saldo/locks+unicidad; NO solo Event OneToOne |
| Dos clientes igual importe | Código/nombre filtran; colisión detectada se aparca; coincidencia no detectada permanece riesgo |
| A tardío con B activo | Reclamación A conservada; no buscar solo monto/pedido activo; timestamp no prueba por sí solo pertenencia |
| Cajero/cliente conocen abono ajeno | Puede superar cotejo; limitar exposición/custodia, auditoría y conciliación detectan parte, no eliminan |
| Teléfono comprometido | Firma del puente puede autenticar datos falsos; revocar y suspender, no garantía bancaria |
| Abono sin aviso | No concluir falta de pago; resolución por movimiento receptor legítimo |

### Puerta piloto/explotación

Piloto limitado puede aprobar automatización ordinaria con riesgo residual expresamente aceptado si los datos reales existen, duplicados/revisiones se identifican, no hay aplicaciones erróneas en casos adversariales, se miden tasa de excepciones/tiempos y se concilia cada movimiento real. No necesita segunda persona por cobro ordinario. Tres yapeos exitosos solo prueban recepción normal, no fiabilidad de asociación o resistencia interna.

Para explotación repetida: además volumen y fallos reales, custodia sostenida, compatibilidad del proveedor, revisión de movimientos con periodicidad aceptada y métricas de apropiación/reclamaciones. Una cuenta personal mezclada con muchos abonos ajenos aumenta el conjunto de candidatos/riesgo. No basta nombrarla “negocio” ni exigir un empleado nuevo para ocultar el límite.

## 3. Recomendación final al agente principal

Con las nuevas prioridades de importe fijo y refund sin efectivo, **priorizar una única integración oficial de cobro por orden, con QR que abra el checkout del comprador, si ese tipo de QR es aceptado y la cuenta DNI se habilita realmente**. El puente queda alternativa condicionada si se exige QR nativo; no recomendar dos canales por defecto para prometer infalibilidad. Ingeniería sólida incluye límites explícitos y recuperación; no hace falta demostrar que todo fallo imaginable es imposible.

El criterio decisivo es un ensayo corto de habilitación/cobro/refund original, no más tablas ni una promesa de nota. Lo que debe cambiar respecto a nuestro dictamen anterior es la obligación de revisión humana en cada aplicación; lo que debe corregirse a Argón es la certeza universal, falsa unicidad del evento y el desconocimiento de costos fijos, requisitos de cuenta y liquidez de reintegros.
