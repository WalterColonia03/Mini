# Contraste para Argón y consulta de elegibilidad — 15/11/2026

Estado: **PROPUESTO / NO ENVIADO**. Este archivo prepara el intercambio; no afirma que Gemini Argón haya recibido o revisado el dictamen. No hay un canal directo identificado con ese agente externo. El usuario puede trasladar este texto y aportar su respuesta, que deberá verificarse nuevamente.

**Base de contraste:** DICTAMEN-PAGOS-ASTRA.md actualizado y su evidencia en `evidencias/PAGOS-AUTO-20261115/`. Se conserva el texto Argón recibido con SHA256 `e62f2adcfd37cee37292f4557025023437f3cd6e0c327ac2a7a7e3fb10f96cdd`. Cualquier respuesta nueva debe identificarse por fecha y archivo; no tratarla como aceptada por su autoría.

**Restricciones confirmadas por el usuario, no inferidas de un agente:** permite evaluar comisión; no tiene RUC; requiere QR mostrado en POS y leído dentro de Yape/Plin, con importe fijado; pagos mixtos y varios aportes; no empleado dedicado a cada validación; cancelación debe tener resolución aunque no haya efectivo. No hay autorización explícita de nuevos yapeos para devolver. No implementar ni afiliar por esta revisión; no modificar 08 ni cerrar etapas.

**Texto para Argón**

Revisa y refuta el dictamen de ASTRA sin tratar sus conclusiones como verdaderas. No necesito acuerdo entre agentes: necesito evidencia por producto, país, cuenta y operación. Responde cada punto con VERIFICADO DOCUMENTALMENTE / PROBADO / INFERIDO / PENDIENTE DE DISPOSITIVO O CUENTA / DECISIÓN DE NEGOCIO. Incluye enlace primario directo y limita exactamente lo que demuestra.

1. ASTRA retiró su recomendación anterior de un delegado por cada pago por ser demasiado costosa y no necesaria universalmente. ¿Qué amenaza concreta quedaría sin control con una pasarela de orden/importe y confirmación autenticada? Propón control que no añada empleado normal. No supongas que automatizar elimina colusión física.
2. Tu descarte total de Izipay por exigir RUC contradice referencias oficiales a DNI: [sitio comercial](https://izipayweb.izipay.pe/) y [términos generales](https://cdnwebb.izipay.pe/content-manager/pdfs/terminos/230/T%C3%A9rminos%20y%20condiciones). Pero esas fuentes tampoco prueban SDK Web QR productivo con DNI. Comprueba **la combinación exacta**, sin saltar entre Izipay Online antiguo, Punto Web, APP, POS, IzipayYA o Interbank Negocios.
3. [Izipay QR](https://developers.izipay.pe/products/pay-with-qr/) describe importe y lectura en billetera; [tabla técnica](https://developers.izipay.pe/value-table/) separa QR de YAPE_CODE y PAGO_PUSH. ¿Existe consulta autenticada de ese pago y contrato de firma, reintento, expiración y transacción? Señala documentación precisa, no solo un ejemplo visual.
4. Sus [condiciones de QR dentro de Interbank Negocios](https://interbank.pe/terminos-y-condiciones-para-el-uso-de-codigo-qr-link-de-pago-y-plataforma-de-pago-en-tiempo-real-de-izipay1) excluyen reversas/anulaciones. La FAQ genérica de SDK menciona refunds. ¿Qué aplica al **QR del SDK Web**? No atribuyas devolución de tarjeta al QR. Necesitamos total, parcial, destino original, saldo requerido y plazos reales.
5. Mercado Pago sí documenta importe/orden y devolución; [alta con DNI](https://www.mercadopago.com.pe/signup/splitter) no prueba elegibilidad productiva del vendedor. ¿Puedes aportar evidencia específica de Checkout Yape productivo para vendedor DNI? No confundas documento del pagador con el del comercio.
6. El usuario precisó escanear dentro de Yape/Plin. QR de URL hacia Checkout Pro es un **cambio de experiencia**, no cumplimiento equivalente. Si lo recomiendas, marca expresamente el cambio pendiente. El [checkout alojado](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/create-order) reduce necesidad de pedir OTP al cajero. No mezcles Orders, Payments y suscripciones.
7. Corrige la comisión de MP con [tarifa pública](https://www.mercadopago.com.pe/herramientas-para-vender/check-out): porcentaje más cargo fijo por cada abono. Calcula S/10 en1,2y6pagos; no asumas mínimos/redondeo. Verifica si un reintegro bruto puede hacerse con neto tras comisión: [refund Orders requiere saldo disponible](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/refunds-cancellations).
8. Tres dígitos no hacen imposible apropiación ni OneToOne a una notificación identifica dinero bancario. Construye un contraejemplo con dos notificaciones del mismo abono o código repetido/conocido. Si propones matching, declara riesgo residual, datos observables reales y tratamiento de ambigüedad. No uses “elegir nombre/hora” como prueba concluyente.
9. Resuelve: se mostró QR15; se cambia a QR10+efectivo5; llega pago del QR15 antiguo. Ocultarlo no es cancelarlo. ¿Qué reserva impide sobrecobro y qué pasa si aun así el proveedor lo acredita? Muestra estado de cada intento y destino del dinero.
10. Resuelve: devolución7 sobre abono10 enviada, timeout; otra devolución7 simultánea. Deben contar reservas inciertas, no solo ejecutadas. Incluye pago previo a Sale, exceso y varios pagadores. No basta lock de Sale ni total de venta.
11. Corrige que Etapa02está cerrada y que las cinco entidades ya existen en sales/models.py: el árbol inspeccionado no demuestra eso. Versiona 08 y producto; distingue evidencia heredada de pruebas ejecutadas por ti.
12. No declares infalibilidad, cero fallos, un segundo o tres segundos sin medición. Propón criterios para **abandonar tu propia opción**. Corrige el presupuesto de ensayo: número real de transferencias, importes, comisiones, fondos para devoluciones y pruebas que requieren pagos adicionales.

Entrega una recomendación priorizada, las objeciones a ASTRA que sobrevivan a evidencia y una tabla de cambios mínimos si ninguna opción satisface todo. No marques PAY-CANAL/PAY-REINTEGRO resueltos ni implementes. Si solo tienes documentación y no cuenta, dilo.

**Consulta preparada para el proveedor — no enviada, sin afiliación**

Somos un proyecto universitario de sistema de ventas de minimarket en Perú, sin RUC ni empresa constituida. Queremos hacer una demostración con pagos pequeños reales entre adultos autorizados. El titular usaría su propia identidad y cuenta receptora, sin prestar credenciales. No buscamos simular una empresa inexistente.

Necesitamos confirmar estas condiciones para **Izipay SDK Web/Punto Web, método QR interoperable**, no solo APP/POS/Link/Yape Code:

- ¿Puede una persona natural únicamente con DNI habilitar producción para este uso? ¿Qué evaluación, documentos y cuenta de abono exige exactamente? ¿Se admite URL HTTPS con subdominio de alojamiento, sin dominio comprado?
- ¿Puede nuestra web en la PC del cajero mostrar QR con importe de cada aporte, escaneable dentro de Yape y Plin, cuyo importe el pagador no pueda editar? ¿Qué billeteras/modalidades son compatibles y qué mínimos/máximos aplican?
- ¿Qué API de consulta y notificación identifica transacción, cuenta receptora, moneda, importe y referencia de nuestra compra? Facilitar documentación de autenticidad, duplicados, actualizaciones, idempotencia, expiración y cancelación. ¿Se puede pagar/reutilizar un QR expirado o previamente pagado?
- Para un pago hecho específicamente por ese QR, ¿hay devolución total y parcial **sobre la operación original**, por API y al pagador original? ¿Qué endpoint, autorización, horario, plazo y estado final aplican? ¿Qué se puede hacer después de liquidar al vendedor? ¿Qué saldo o reserva exige? ¿Se devuelven comisiones? ¿En qué difiere de las restricciones de QR en APP/POS e Interbank Negocios?
- ¿La tarifa incluye porcentaje, cargo fijo por aporte, IGV, afiliación, mantenimiento, retiro/liquidación o cargo de devolución? ¿Existe mínimo de transacción o de comisión? Separar entorno sandbox y producción.

Por favor responder por esa modalidad con enlace/documento aplicable. Una respuesta comercial genérica de “DNI, QR y reembolsos” no permite comprobar que las tres capacidades se puedan contratar juntas. No estamos solicitando abrir, afiliar o habilitar una cuenta mediante esta consulta.

**Cómo cerrar el contraste**

No votar entre agentes. Registrar por punto: afirmación, fuente, alcance, contraejemplo, prueba faltante y consecuencia. Si ambos discrepan pero ninguno puede observar la cuenta, la salida es un ensayo/consulta delimitado, no repetir búsquedas indefinidamente. Aprobación del usuario autoriza decisiones; respuesta del proveedor delimita capacidades; pago/reintegro real prueba el comportamiento concreto. Ninguna de esas evidencias sustituye a las otras.
