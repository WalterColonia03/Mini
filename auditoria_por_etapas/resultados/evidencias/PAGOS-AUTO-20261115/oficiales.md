# Fuentes oficiales: automatización de pagos Perú

Fecha de consulta: 2026-11-15. Autor de esta revisión documental: agente canales_oficiales_auto. Alcance: fuentes públicas oficiales; no acceso a cuentas, teléfonos, credenciales ni producto. No transferencias ni afiliaciones. Ninguna capacidad fue PROBADA en dispositivo o cuenta. No se modifica planificación aceptada.

## Candidato principal condicionado: Mercado Pago Checkout Pro alojado

**VERIFICADO DOCUMENTALMENTE:** Checkout Pro Perú incluye Yape, pago en entorno de Mercado Pago y opción de invitado. La documentación nueva tiene dos familias, Preferences API y Orders API; seleccionar una y no mezclar endpoints ni plazos.

- [Resumen Checkout Pro Orders Perú](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/overview).
- [Página comercial Perú](https://www.mercadopago.com.pe/herramientas-para-vender/check-out): tarifa publicada 3,49 % + S/ 1 por cobro con disponibilidad inmediata; 3,29 % + S/ 1 con disponibilidad en 14 días. Es comisión de cobro; no incluye costos del proyecto. Validar tarifa efectiva en cuenta y tratamiento de comisión al reembolsar.
- [Crear order](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/create-order): server-side, total_amount, external_reference, X-Idempotency-Key; respuesta id y checkout_url; país/moneda/dominio dependen de cuenta vendedora. processing_mode=manual para Pro. Guardar identificador proveedor por intento y verificar importe/moneda/cuenta al acreditar.
- [Notificaciones Pro Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/notifications): HTTPS POST de eventos de orden, firma secreta para autenticidad y consulta GET /v1/orders/{order_id} para recuperación si faltan notificaciones. La muestra contiene referencias de Chile: no copiar moneda ni datos de muestra como capacidades de Perú. La solución se documenta en sitio Perú.
- [Reembolsos Pro Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/refunds-cancellations): reembolso total o parcial por POST /v1/orders/{order_id}/refund, sobre operación original; saldo disponible suficiente; 180 días desde aprobación; múltiples parciales acumulados no mayores al pago. Para medios distintos de tarjeta de crédito indica cuenta del pagador. No documenta en esta página un plazo de llegada específico de Yape ni su pantalla/destino exacto: PENDIENTE DE CUENTA/ENSAYO.
- [Salir a producción Pro Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/go-to-production): activar entorno, declarar sector y sitio web, aceptar términos, HTTPS, idempotencia, webhook y flujos de cancelación/reembolso probados. No declara que toda cuenta DNI quede habilitada ni impone expresamente RUC en estos pasos públicos.
- [Alta de cuenta Mercado Pago Perú](https://www.mercadopago.com.pe/signup/splitter): cuenta personal con DNI y cuenta negocio con RUC/representación legal. **No demuestra elegibilidad productiva de Checkout Yape de una cuenta personal.** Verificar permisos efectivos, identidad validada, recepción de Yape, límites/retiros y cuenta receptora autorizada sin abrir ni afiliar cuentas por esta revisión.

**INFERIDO / PROPUESTO:** mostrar un QR de URL HTTPS que lleve a un intento creado por el servidor y redirija a checkout_url ofrece importe fijado, asociación de orden, verificación de proveedor y devolución sobre la operación original. El OTP lo manejaría el checkout alojado. Es QR de enlace leído con cámara, no QR interoperable de transferencia leído dentro de Yape. Necesita aceptación expresa de experiencia QR y comisión; no presentar ambas modalidades como equivalentes. Saldo recibido en cuenta vendedora Mercado Pago y liquidación/retiro deben quedar autorizados: no es abono directo al Yape receptor existente.

**PENDIENTE DE CUENTA/ENSAYO:** DNI → vendedor productivo Checkout Pro → Yape disponible → pago autorizado → notificación/API → reintegro parcial/total → destino y plazo real → retiro a cuenta autorizada. También importe mínimo, comportamiento de order ya pagada/reusada, expiración, carrera cancelar/pagar, tarifa y comisión reembolsada. No prometer que un QR de importe fijo elimina todo doble cobro: varios intentos concurrentes requieren reserva de saldo, cancelación y conciliación.

La alternativa Checkout API propia se documenta oficialmente con teléfono y OTP, pero no es primera opción frente al checkout alojado: [Yape Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-api-orders/payment-integration/websites/yape). No guardar OTP ni pedirlo al cajero. La familia Payments tiene condiciones distintas: [Reembolsos Payments](https://www.mercadopago.com.pe/developers/es/docs/checkout-api-payments/payment-management/cancellations-and-refunds). No trasladar su plazo de 90 días a Orders.

## Alternativas que corrigen descartes demasiado generales

**VERIFICADO DOCUMENTALMENTE:** BBVA Perú ofrece API QR dinámica para negocios, abono en tiempo real y conciliación. Eso demuestra que existe automatización oficial QR en Perú; no demuestra tarifa cero, contratación sin RUC ni acceso autoservicio para este proyecto.

- [APIs BBVA Perú](https://www.bbva.pe/empresas/apis-bbva.v2.html).
- [Artículo oficial sobre API QR](https://www.bbva.com/es/pe/innovacion/bbva-impulsa-la-transformacion-digital-empresarial-a-traves-de-sus-apis/).
- [QR BBVA empresas](https://www.bbva.pe/empresas/productos/cobros-y-pagos/soluciones-de-cobro-qr.html).

**VERIFICADO DOCUMENTALMENTE:** App Interbank Negocios permite registro con DNI vigente y celular; también enumera modalidades RUC10/RUC20. izipayYA se actualiza a esta app. Plin sin comisión de cobro no equivale al producto QR Izipay con tarifa. No descartar toda la app por RUC o por la tarifa de otra modalidad.

- [Interbank Negocios](https://interbank.pe/negocios/zona-digital/interbank-negocios).
- [Plin Negocios](https://interbank.pe/canales-digitales/plin/plin-negocios): QR para recibir Yape/Plin y sin comisión en Plin; no encontré API/webhook público ni vinculación automática de orden acreditada para la modalidad DNI.
- [Condiciones QR/Link Izipay dentro de Interbank Negocios](https://interbank.pe/terminos-y-condiciones-para-el-uso-de-codigo-qr-link-de-pago-y-plataforma-de-pago-en-tiempo-real-de-izipay1): producto distinto. No extrapolar condiciones a Plin ni viceversa.

## Yape común

**VERIFICADO DOCUMENTALMENTE:** [Pago con QR Yape](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/31--como-hago-un-pago-con-qr) describe escanear y luego introducir importe. QR entre personas utiliza código de seguridad corto compartido en constancia y aviso. No es identificador universal. No hallé soporte oficial de QR personal con monto fijo inmodificable y referencia de pedido propagada a notificación receptora. No asumirlo a partir de estándares EMV.

No documentar capacidades de Ayudantes (campos de push, permanencia, ID transaccional, reversa/API) como probadas sin inspección de cuenta/dispositivo. [Qué pueden hacer ayudantes](https://www.yape.com.pe/preguntas-frecuentes/yape-empresa/que-podran-hacer-mis-ayudantes) es fuente de capacidades visibles, no contrato de API.

## Conclusión de investigación

**PROPUESTO:** bajo aceptación de comisión y QR de enlace, priorizar prueba pequeña de Checkout Pro alojado con Orders API. Resuelve documentalmente importe servidor, asociación a orden y canal de reintegro original. No necesita otro empleado dedicado ni Android receptor en flujo normal. El bloqueo decisivo actual es elegibilidad productiva de cuenta propia con DNI y comportamiento real Yape/reembolso. Si exige QR nativo dentro de Yape, esa solución no satisface la experiencia: verificar contratación de API QR empresarial; hoy no hay evidencia de acceso compatible sin RUC para este proyecto. No usar la falta de documentos como prueba de imposibilidad universal.
