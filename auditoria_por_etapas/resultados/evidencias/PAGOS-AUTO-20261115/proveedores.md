# Investigación de proveedores para verificación automática de Yape

Fecha de consulta: 2026-11-15, America/Lima. Alcance: páginas públicas primarias de proveedores; lectura documental, sin instalación, registro, afiliación, contacto comercial, transferencias ni llamadas autenticadas. Responsable de esta revisión: agente de investigación independiente `/root/alternativas_auto`.

Estado: **PROPUESTO / VERIFICADO DOCUMENTALMENTE**, exclusivamente respecto de lo que publican las fuentes. **Ningún proveedor fue PROBADO** en el Galaxy A52s, en la cuenta del usuario ni con el producto. Este documento no modifica requisitos aceptados, HU, producto ni etapas. No determina elegibilidad financiera por la ausencia de un campo RUC en una página comercial.

## Resultado práctico

Sí existen productos peruanos que automatizan la captura y distribución de avisos Yape; por tanto, exigir una segunda persona por cada cobro no es una consecuencia inevitable de usar Yape. Sin embargo, capturar avisos y asignar inequívocamente dinero a una compra son capacidades distintas. Comprar un servicio denominado «API Yape» no convierte su origen Android en una API bancaria.

**Recomendación provisional:** evaluar un puente propio mínimo y usar Tingu Alerta como comparación técnica, no contratar una integración basándose únicamente en su publicidad. Tingu tiene el contrato técnico público más detallado de los puentes examinados, pero su acceso API requiere habilitación separada y sus términos dejan pendiente el uso de la alerta como comprobación única. BiPe presenta una asociación automática incompatible con conservar precios y resolver empates de forma segura. Yapay demuestra un patrón de operación existente, pero no quedó documentada una API para Django con garantías suficientes. Ninguno autoriza reintegros bancarios ni resuelve por sí solo la apropiación de abonos por un cajero malicioso.

## Comparación breve

| Candidato / identidad publicada | Fuente real y costo publicado | Cuenta / integración | Resultado de esta revisión |
|---|---|---|---|
| Tingu Alerta / Grupo Softtech Soluciones | Notificaciones del teléfono receptor; suscripción desde S/19/mes. API y webhook se habilitan aparte, no están incluidos en ningún plan. | Android; REST, Socket.io, webhook. Requisito RUC no aparece en elegibilidad publicada. | Mejor documentación técnica encontrada; precio total API y autorización contractual pendientes. No acredita orden bancaria. |
| BiPe Alerta / marca BiPe; razón social no verificada | Notificaciones del celular; API y webhook restringidos a Enterprise. Precio actual no verificable en la página pública consultada. | API de consultas e intenciones; requisitos DNI/RUC pendientes. | No adoptar su emparejamiento por monto: altera céntimos o selecciona la intención más antigua. |
| Yapay / marca Yapay independiente | Avisos Android, Sheets y distribución; S/20 mensual Estándar, S/25 Premium. | No se halló contrato público de API/webhook para backend propio en las páginas examinadas. RUC no demostrado. | Útil para alertas e historial; insuficiente como integración automática monetaria validada. |
| VerifyApp / Nexi Estudio | Captura de avisos; S/5/mes base. API Beta en plan personalizado de precio no publicado. | Android; monitor web. Elegibilidad DNI/RUC y contrato API pendientes. | Alternativa comercial para ensayo, todavía sin contrato público suficiente para integración. |
| Taypi / marca Taypi | QR por cobro y webhook; 2.50% + S/0.20 + IGV por operación publicada. | RUC activo 10/20; sandbox y producción diferenciados. | Mejor vínculo proveedor/pedido, pero incompatible con cero comisión y ausencia de RUC. Aceptar comisión por sí solo no elimina el requisito RUC. |

Los costos indicados son del servicio anunciado, no del conjunto teléfono, conectividad, alojamiento, implementación y mantenimiento. Una prueba gratis limitada no equivale a operación gratuita permanente. Las denominaciones comerciales no acreditan por sí mismas identidad jurídica, solvencia, custodia ni autorización de Yape/BCP.

## 1. Tingu Alerta: capacidades y límite contractual

**VERIFICADO DOCUMENTALMENTE:** la web describe captura en el teléfono del dueño, reenvío al personal y QR guardado. Publica prueba de 100 alertas/7 días, Básico S/19 (500 alertas), Business S/49 y Enterprise S/89. Declara independencia de Yape, Plin y BCP. Sus afirmaciones de dos segundos y de ausencia de pérdida son publicidad, no mediciones nuestras. La página contiene tanto el mensaje de que ausencia de sonido implica ausencia de pago como una FAQ que admite retrasos de conexión/permisos; no usar la primera afirmación como regla de caja. [Producto y precios](https://tingualerta.com/).

**VERIFICADO DOCUMENTALMENTE:** API y webhook requieren activación separada y no se incluyen en planes. REST entrega ID de alerta, monto, nombre, código de seguridad, fecha, billetera y sucursal. Webhook incluye HMAC del cuerpo; admite eventos de prueba, reintentos y deduplicación por ID. No documenta referencia bancaria de pedido. Su histórico se limita al plan. Si una sucursal solicitada no pertenece a la cuenta, Socket.io puede suscribir todas; el servidor del minimarket debe validar destinatario y sucursal. El ejemplo responde antes del procesamiento: en nuestro diseño debe persistirse duraderamente el evento antes de ACK. [Documentación API](https://tingualerta.com/desarrolladores).

**VERIFICADO DOCUMENTALMENTE:** los términos describen un servicio de notificación que no procesa pagos; enumeran Android 8+, permisos y datos veraces, sin RUC explícito. Excluyen garantía de disponibilidad, exactitud e integridad; atribuyen al usuario verificar y confirmar cada operación directamente en la billetera. También restringen automatización no autorizada. La API documentada permite integraciones habilitadas, pero no prueba aceptación contractual de liberar mercadería basándose exclusivamente en ella. [Términos, §§2–6 y 9–10](https://tingualerta.com/terminos-de-servicio).

**PENDIENTE DE CUENTA/PROVEEDOR:** costo total de activación, modalidad personal admitida, condiciones para el uso propuesto y reglas de recuperación de avisos ausentes. **PENDIENTE DE DISPOSITIVO:** captura con pantalla bloqueada, suspensión, reinicio, actualización, revocación y campos reales. **INFERIDO:** HMAC autentica el puente, no al banco; un ID de alerta no demuestra que avisos repetidos/actualizados sean distintas transferencias. Un histórico del mismo puente no verifica dinero que nunca produjo un aviso.

Privacidad publicada: extrae monto, nombre, código si existe, billetera y fecha; afirma limitar lectura a apps configuradas. Los datos pasan por su servidor, a diferencia de un puente propio directo al backend. Esta es una declaración del proveedor, no una auditoría del APK ni de su infraestructura. [Privacidad](https://tingualerta.com/politica-de-privacidad).

## 2. BiPe Alerta: la «referencia» no resuelve el vínculo bancario

**VERIFICADO DOCUMENTALMENTE:** API/webhook solo Enterprise; tokens para consultas; intenciones con referencia aportada por el comercio. La asociación se hace por importe: `montoUnico:true` resta céntimos; desactivado, selecciona la intención pendiente más antigua. Publica cancelación de intención, no reintegro, y rechazo al cancelar una intención pagada. Los IDs descritos corresponden al servicio/aviso. La documentación recomienda autenticación entrante, pero no define una firma bancaria. Precio Enterprise, requisitos RUC y términos aplicables no quedaron comprobados; la portada devolvió error durante la consulta. [Documentación primaria](https://www.bipealerta.com/Documentacion.html), [portada consultada](https://www.bipealerta.com/).

**INFERIDO:** una etiqueta `Referencia` agregada después de comparar montos no transporta una referencia del pagador al banco. Dos pedidos de S/10 pueden intercambiarse. Reducir uno a S/9.99 exigiría una política comercial nueva y aún no elimina abonos ajenos, pagos tardíos o reuso futuro del importe. El estado `PAGADO` del proveedor no basta para aceptar esa asociación. **DECISIÓN PROPUESTA:** descartar su asignación automática publicada para este proyecto; eventualmente evaluar solo observaciones sin asociar, tras resolver costos, identidad y seguridad.

## 3. Yapay: producto operativo anunciado, contrato técnico insuficiente

**VERIFICADO DOCUMENTALMENTE:** precios mensuales Estándar S/20 y Premium S/25, prueba 7 días; alertas, historial, Google Sheets y avisos al personal. La FAQ reconoce dependencia de permisos y red y pide revisar Yape si hay duda. No se halló en las páginas consultadas una API de intenciones ni esquema público de webhook autenticado. Ausencia de documentación encontrada no demuestra inexistencia. [Producto y precios](https://yapay.net.pe/).

**VERIFICADO DOCUMENTALMENTE:** privacidad identifica lectura de notificaciones del paquete Yape, extracción de nombre/monto, registro en Sheets y envío mediante ntfy. Describe transporte con la palabra HTTP; no acredita TLS de extremo a extremo. **PENDIENTE:** aclarar si es redacción genérica/desactualizada o transporte sin cifrar, así como autenticación de tópicos, retención, API y compatibilidad actual. No inferimos una vulnerabilidad comprobada. [Privacidad](https://yapay.net.pe/privacy-policy.html).

**INFERIDO:** exportar filas a Sheets no crea una referencia bancaria ni una operación reversible. Como componente de cobro inmediato necesita además ID estable, reintentos verificables y pruebas de aislamiento. **DECISIÓN PROPUESTA:** mantener como referencia de funcionamiento, no elegirlo aún como dependencia del núcleo monetario Django.

## 4. VerifyApp: base económica, integración no cotizada

**VERIFICADO DOCUMENTALMENTE:** Nexi Estudio declara una herramienta independiente que lee notificaciones en Android sin pedir claves de Yape; ofrece monitor web. Plan base S/5/mes y cinco días de prueba; API Beta solo en plan personalizado. No se encontró en la página contrato API, identificador bancario, firma, política de reintentos ni tarifa de esa integración. Sus garantías comerciales de ausencia de fraude no están probadas. [Sitio primario](https://verifyapp.nexiestudio.com/).

**PENDIENTE:** costo completo, requisitos de alta personal, condiciones, prueba Android y contrato técnico. **INFERIDO:** menor precio de alertas no demuestra menor costo de integrar ni mayor confianza; introducir otro servidor añade custodia de datos y dependencia operativa.

## 5. Taypi: referencia de pasarela, no alternativa compatible actual

**VERIFICADO DOCUMENTALMENTE:** publica QR individual aceptable desde Yape/Plin, RUC activo 10 o20 y comisión de 2.50% + S/0.20 + IGV. [Preguntas frecuentes](https://taypi.pe/preguntas-frecuentes/). Documenta sandbox, creación de pagos con `reference` y webhook HMAC con `payment_id`, monto y estado. [Integración](https://docs.taypi.pe/integracion).

**PENDIENTE DE CUENTA:** afiliación, liquidación, términos específicos de reembolso y funcionamiento real. **INFERIDO:** la asociación a una orden nativa del proveedor es una ventaja estructural frente al emparejamiento posterior por monto. **DECISIÓN PROPUESTA:** no recomendar bajo cero comisión/sin RUC; mantener solo como contraste si ambas restricciones cambian explícitamente. Una comisión aceptable no autoriza contratarla ni habilita por sí sola reembolsos.

## Límites comunes que ninguna publicidad elimina

1. **Autenticidad:** comprobar app emisora, firma de paquete y teléfono confiable. El texto «Yape» dentro de un aviso no basta. Un webhook solo lleva la confianza de quien lo origina.
2. **Asociación:** recibir S/10 prueba un evento monetario bajo ciertas condiciones, pero no qué compra lo merece. No adjudicar por ser la venta activa, por antigüedad ni por importe aislado. Código corto, nombre y hora reducen candidatos; no prueban exclusividad universal ni impiden toda colusión.
3. **Aplicación única:** mantener ID propio, ID del proveedor y evidencia original separados; persistencia, restricciones y transacción de base de datos. Deduplicar webhook no basta para deduplicar dos avisos del mismo abono.
4. **Fallos:** teléfono y puente sin señal deben marcar canal degradado; ausencia de aviso no autoriza pedir otro pago ni prueba impago. Usar conciliación, no una nueva venta para absorber un aviso tardío.
5. **Reintegros:** ninguno de estos puentes demuestra devolución bancaria de una transferencia Yape. Cancelar intención/venta no devuelve dinero. Un eventual efectivo delegado exige política aceptada, saldo a favor, evidencia, caja, identidad y límite de concurrencia.

Estas son inferencias de arquitectura aplicadas a la documentación, no hallazgos de explotación de proveedores. No se instalaron APK ni se inspeccionaron secretos ni cuentas.

## Ensayo que discrimina proveedor de publicidad

**PROPUESTO:** comparar captura propia mínima con un solo puente documentado en el Galaxy A52s/Android14, usando la cuenta autorizada que realmente vaya a recibir. Antes de pagos reales: comprobar origen de app, permisos, payload, diferenciación test/producción, autenticación, persistencia y exportación. Después, ensayo autorizado con importes pequeños: dos pagos iguales, dos pagadores, S/3 + S/7, aviso repetido, teléfono sin red y reiniciado, servidor sin respuesta, compra cancelada y aviso tardío. Registrar recepción bancaria observada separadamente del aviso, transporte y aplicación local.

**Continuar:** ningún falso positivo, ninguna doble aplicación, todo aviso perdido o ambiguo identificado como excepción recuperable; condiciones y costo API aclarados; asociación automática defendible sin céntimos artificiales ni selección por antigüedad. **Cambiar:** no existe dato suficiente para distinguir los casos adversarios, exige intervención ordinaria no aceptada, no recupera pérdidas, exige acceso bancario inseguro, o sus términos no permiten el uso requerido. Pasar pruebas funcionales no demuestra una garantía absoluta; documentar población pequeña y riesgo residual.

La existencia de estos servicios permite investigar automatización con seriedad. No demuestra que alguna oferta ya satisfaga simultáneamente todas las restricciones y amenazas del proyecto. La decisión siguiente es un ensayo delimitado, no investigación indefinida ni implementación de cobros reales por anticipado.
