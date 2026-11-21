# Revisión de la Opción A de Argón y propuesta A corregida

Fecha: **15/11/2026, America/Lima**. Resultado: **PROPUESTO; no aceptado ni implementado**. Complementa y corrige, donde se indica, `DICTAMEN-PAGOS-ASTRA.md`. No modifica 08 ni sus vistas, producto o estado de etapas.

**Dictamen: no confirmar la Opción A completa ni trasladarla a 08 como aceptada. Recomiendo A corregida (A′): ajustar únicamente efectivo todavía pendiente, conservar toda recepción real, reservar devoluciones antes de ejecutarlas y mantener cualquier importe no devuelto como una obligación abierta. Un vale o una tarea para ADMIN no solucionan por sí mismos la falta de un canal de devolución.** Mantener la constancia interna de RN-13/RN-26 sí es compatible con el alcance vigente.

El rumbo de cobro continúa siendo **QR oficial por intento y por importe del aporte**, con verificación autenticada y referencia de pedido; primero comprobar Izipay SDK Web QR para esta cuenta y uso. Su disponibilidad con DNI y la devolución del QR concreto siguen pendientes. La revisión no autoriza afiliación ni contratación. Mercado Pago sigue condicionado a aceptar otra experiencia de pago; un puente de notificaciones no demuestra el QR de importe fijo requerido.

## 1. Evidencia y autoridad

**VERIFICADO DOCUMENTALMENTE (VD):** adjunto completo recibido ahora, fuentes enlazadas y archivos locales inspeccionados. **PROBADO (PR):** solo ejecuciones propias descritas abajo. **INFERIDO (IN):** razonamiento técnico. **PENDIENTE DE DISPOSITIVO O CUENTA (PD):** comportamiento o habilitación que requiere proveedor/cuenta/ensayo. **DECISIÓN DE NEGOCIO (DN):** política aún por aceptar. La inspección de código no se etiqueta aquí como prueba funcional.

Se conserva evidencia de las revisiones anteriores; no se repiten ni se atribuyen a esta pasada sus pruebas. En esta pasada se revisaron el nuevo adjunto, el PDF v307, documentación de tarifas/reembolsos y valores de SDK; se contrastaron tramos monetarios de 08 y código de caja/ventas. Una revisión cruzada independiente del adjunto detectó ocho objeciones, contrastadas en este informe. No hubo comunicación directa con Gemini: el contraste se hizo sobre el texto suministrado por el usuario.

Referencias de corte:

- 08 SHA-256: `c0aa262b2dceba783ffa08e61bcca985857d777f5ef38be7749c4dd99d47e632`.
- 21 SHA-256 real: `52daf4a562991ca9327b3859021b03f92c3477d086c91cee5c18cbe4da1d1eee`. El adjunto presenta una diferencia en ese hash; no reemplaza la lectura del archivo.
- HEAD de producto: `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, con cambios preexistentes. Manifiesto de 232 archivos seleccionados: `6fec70fa58a357f7b679656d29ec722daff62b495da075c995869c3db0214fea`. Un hash de ZIP no identifica por sí solo este árbol de trabajo.
- Adjunto de esta pasada: SHA-256 `7e25e9bb7c4003775334944abaebc4e659d3378cd3721f1304cfba343f5386a7`.
- Dictamen anterior preservado: SHA-256 `cb3d95860f458c8d6ee9a79d8ab2c7226719037f3d8581cbc42413aa5bbd6155`.
- Carpeta de evidencia: `evidencias/OPCION-A-20261115/`. Contiene copia del adjunto y del dictamen anterior, PDF y hash, línea base, siete contraejemplos aislados y validación final.

**Sin cambios de autoridad:** evaluar comisión está ACEPTADO; una tarifa/proveedor concreto, nuevos yapeos para devolver, vales, plazos y facultades de retiro no lo están. No se añade un cuarto rol. Etapa 01 conserva ingreso/bloqueo/acceso; Etapa 02, sesión/personal, sigue PARCIAL. No se reabre ni cierra otra etapa.

## 2. Qué confirmar y qué corregir del nuevo texto

| Afirmación | Dictamen y evidencia | Efecto práctico |
|---|---|---|
| Izipay ofrece afiliación con DNI y documenta QR interoperable | **VD correcta en esos alcances separados; PD su combinación productiva.** [Portal comercial](https://izipayweb.izipay.pe/), [métodos del SDK](https://developers.izipay.pe/value-table/) | No descartar Izipay por RUC en general ni prometer SDK QR disponible para esta cuenta |
| El PDF v307 prueba que los comercios DNI no pueden usar comercio electrónico y tienen límite S/20.000 | **Incorrecta atribución de los pasajes localizados.** La restricción de comercio electrónico está en Google Pay, p.66; el tramo S/20.000 aparece en licencias Ari, pp.45–46. [PDF oficial](https://cdnwebb.izipay.pe/content-manager/pdfs/terminos/307/terminos) | Pedir cláusula y producto exactos; retirar esta supuesta prueba general |
| Izipay tiene exclusiones QR de anulación/extorno | **VD correcta, con alcance.** P.12 PPTR y p.33 APP IZIPAY contienen restricciones. No constituyen por sí solas respuesta contractual del SDK Web. [PDF oficial](https://cdnwebb.izipay.pe/content-manager/pdfs/terminos/307/terminos) | Mantener bloqueada la promesa de refund QR hasta confirmación de modalidad y ensayo |
| Todo QR peruano carece de devolución automática | **No demostrado.** IN excesiva a partir de contratos de productos específicos | No convertir una limitación de proveedor en imposibilidad universal |
| `YAPE_CODE` está disponible solo en SDK Web | **Incorrecta.** La [tabla oficial](https://developers.izipay.pe/value-table/) dice todos los SDK; `QR` sí figura solo Web | No confundir QR interoperable, código Yape y Plin push |
| MP inmediato cobra 3,49% + S/1 por abono | **VD correcta para tarifa pública consultada.** [Checkout Perú](https://www.mercadopago.com.pe/herramientas-para-vender/check-out) | El fijo penaliza fuertemente dividir tickets pequeños |
| Los netos de 1, 2 y 6 pagos y su IGV son importes efectivos ya comprobados | **Incompleta.** Cálculo agregado aproximado; no se verificó redondeo por operación ni tratamiento tributario de la tarifa aplicable | Cotización/estado de cuenta deben confirmar netos; no extrapolar impuestos de otro producto |
| MP exige saldo disponible para reembolsar | **VD correcta.** [Reembolsos Checkout Pro Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/refunds-cancellations) | Una API no aporta liquidez. La fuente no demuestra por sí sola el campo exacto `available_money`, la liberación de comisiones ni el flujo real Yape de esta cuenta |
| MP Yape equivale al QR escaneado dentro de Yape/Plin solicitado | **Incorrecta equivalencia.** Su [integración Yape](https://www.mercadopago.com.pe/developers/es/docs/checkout-api-orders/payment-integration/websites/yape) usa celular y código de autorización | Sigue siendo alternativa solo con cambio de experiencia aceptado |
| Quince segundos permiten descartar duplicados y 180 segundos delimitan identidad | **IN incorrecta como garantía; PR contraejemplos A03/A04** | Coincidencia implica sospecha, no prueba de un único abono |
| `SUPERSEDED_WATCHED` evita doble cobro al reemplazar QR15 por QR10 | **IN incompleta; PR A02** | Vigilar no invalida QR15. Puede quedar exposición pagable de S/25 |
| Reservar reintegro antes de llamar al proveedor y conservarlo tras timeout | **IN correcta como diseño PROPUESTO** | Exigir consulta/reconciliación para liberar; no confundir con locks ya probados en PostgreSQL |
| `executed_refunds` puede sumar dinero devuelto, vales y nuevas compras | **IN incorrecta semántica; PR A07** | Separa dinero devuelto, saldo pendiente y aplicación a ventas; evita doble contabilización |
| ID externo único o consulta autenticada son alternativas equivalentes | **Incorrecta.** IN: un atacante puede inventar un ID todavía no usado | Autenticidad y unicidad son requisitos acumulativos |
| Lock de caja demuestra billetes suficientes | **Incorrecta.** VD local/IN; PR A06 | Protege saldo contable y reservas; no observa efectivo físico ni denominaciones |
| Vale RC o liquidación ADMIN resuelven automáticamente una cancelación sin efectivo | **DN pendiente e IN incompleta** | Hay deuda hasta ejecución o una alternativa voluntaria correctamente registrada |
| RN-13/RN-26 mantienen constancia interna | **VD correcta respecto a 08** | Conservar leyenda y alcance; no añadir factura fiscal ni integración SUNAT |

El PDF guardado tiene 108 páginas, SHA-256 `11edfa45f57b53181637a3050490b65626b0542fb087ce87edcf1788116cc0f8`. La fecha de una campaña interna no acredita la fecha global de versión. Tampoco usar promociones antiguas contenidas en él como tarifa vigente del SDK. Esta corrección acota evidencia, no interpreta que la devolución QR esté habilitada.

**PR matemático, no factura del proveedor:** con seis aportes de S/1,67, S/1,67, S/1,67, S/1,67, S/1,67 y S/1,65, la fórmula indicada suma S/6,349 sin redondear. Redondear al final da S/6,35; redondear cada cargo a céntimos da S/6,36. Por tanto, el número exacto depende de reglas no ensayadas. Aplicar además 18% es un escenario condicionado a que corresponda, no una verificación de impuestos por esta lectura.

## 3. A′: política y flujo recomendados, todavía PROPUESTOS

### 3.1 Reparto, cobro y exceso

**IN/DN:** antes de generar QR se elige cuánto pagar digitalmente. Venta S/15: QR S/10 y efectivo S/5. El servidor controla el importe y receptor. Un QR fijado por el proveedor reduce errores de importe, pero no evita pagos dobles, tardíos ni cancelaciones.

| Hecho real | Resultado A′ |
|---|---|
| Compra S/15; llegaron S/15 digitales; efectivo S/5 todavía no recibido | Aplicar S/15 y reducir pendiente de efectivo a cero. Mostrar el cambio; preservar intento/reparto anterior. Si el aporte proviene de tercero, respetar su destino autorizado y no apropiárselo por importe |
| Compra S/15; llegaron S/15 digitales y ya se recibieron S/5 en efectivo | Registrar S/20 recibidos, aplicar S/15 y mantener S/5 por resolver. No borrar recepción ni convertir automáticamente excedente digital en vuelto |
| Compra S/15; QR S/10 confirmado; cliente entrega billete S/10 | Efectivo aplicado S/5 y vuelto debido S/5. Registrar recepción y entrega; no declarar vuelto entregado si faltan billetes |
| Compra S/10; aportes S/3 y S/7 de teléfonos distintos | Dos abonos con identidad/origen propios, dos aplicaciones al mismo pedido; una venta. Una eventual devolución conserva el vínculo con cada aportante |
| Solo llegaron S/3 y cliente cancela | Cancelar el pedido no borra los S/3: crear obligación de reintegro S/3 y cerrar intentos restantes con vigilancia de pagos tardíos |
| Pago completo; falla confirmación técnica | Estado CUBIERTO_PENDIENTE_CONFIRMACION; recuperar idempotentemente. No solicitar otro pago. Si no puede completarse, resolver saldo según política |

**Cambio de QR:** no emitir un nuevo intento pagable contra la misma parte del saldo mientras el anterior siga pudiendo cobrarla, salvo riesgo expresamente aprobado y devolución financiada. Una petición de cancelación deja `CANCEL_REQUESTED/WATCHED`; solo una respuesta concluyente según contrato permite liberar su reserva. Ocultar QR, desconectar navegador o vencer un temporizador local no lo invalida externamente. Un pago tardío se atribuye al intento original y reevalúa su saldo; nunca a la siguiente compra abierta. No usar nombre/importe/hora como identidad universal.

**Pedido incierto:** cajero ve importe confirmado, pendiente, intentos de resultado desconocido y saldo por devolver por separado. Acciones propuestas: «Consultar estado», «Aparcar pedido» y, con permiso, «Solicitar reintegro». Mensaje propuesto: «El estado del pago está pendiente de comprobación. No solicites otro pago por este importe». Puede atender otro pedido sin entregar mercadería pendiente. Cada acción/mensaje necesita CA/CP antes de implementarse.

### 3.2 Obligación de devolución y caja

**IN/DN:** dinero sobrante o una cancelación con dinero recibido generan una obligación identificada. Registrar motivo, importe, pedido, abonos de origen, beneficiario verificable, responsable y estado. No pagar a quien solo conoce el importe o presenta una captura. El comprador y el pagador pueden ser personas distintas.

Prioridad propuesta:

1. Reintegro sobre operación original cuando el producto lo permita, con reserva y estado externo comprobable.
2. Efectivo, solo si se acepta esa política: saldo contable suficiente después de reservas, disponibilidad física comprobada, autorización independiente para la excepción, movimiento de caja y constancia de entrega. El permiso puede delegarse a una persona existente ADMINISTRADOR o ALMACENERO, según se apruebe. No exige una persona adicional verificando cada venta. No presupone que hoy exista ese permiso.
3. Si ninguno puede ejecutarse: **REINTEGRO_PENDIENTE**, con canal y compromiso concretos antes de ofrecerlo como solución operativa. Puede emitirse constancia de la deuda, que no diga «devuelto». Aplicarla a otra compra o convertirla en vale exige elección informada del cliente y política aceptada; no es la salida automática.

Recomiendo **posponer el vale canjeable** del primer incremento. Añade titularidad, saldos, canjes parciales, pérdida de código, concurrencia y fraude propios sin aportar liquidez. Una constancia de obligación pendiente sí conserva evidencia. `RC-########` puede ser un identificador interno provisional, pero no prueba identidad ni debe permitir cobrar por conocerlo. No llamarlo «Nota de Crédito» fiscal.

«Liquidación externa de ADMIN» debe sustituirse por datos concretos: canal autorizado, cuenta/fondo que paga, persona facultada, disponibilidad sin el dueño, plazo aceptado, beneficiario y evidencia de ejecución. El rol informático ADMIN no otorga poder bancario ni dinero. La prohibición vigente de nuevos yapeos no puede ocultarse detrás de esa etiqueta.

**Límite irreductible:** caja sin efectivo + proveedor sin reintegro original + prohibición de transferencias nuevas es incompatible con prometer devolución monetaria inmediata. El cambio mínimo sería aceptar devolución diferida con canal y fondos definidos, autorizar otro canal de devolución, o elegir un producto que reembolse el pago original y mantener saldo utilizable. Ninguno se adopta automáticamente. Si la inmediatez es imprescindible, el canal sin reversa no pasa la selección.

No se inventan topes, plazo de deuda ni importes de reserva como decisiones aceptadas. Recomiendo que la política defina límites por operación y acumulado por empleado/turno, devolución al origen, prohibición de aprobar la propia excepción y revisión posterior de anomalías. Los valores dependen del ticket y fondo real disponibles. La colusión o entrega física no registrada siguen siendo riesgos.

### 3.3 Libro monetario y reservas

**IN/PROPUESTO:** separar aviso, abono comprobado, aplicación al pedido, obligación de devolución, intento de devolución y salida ejecutada. La venta confirmada referencia aplicaciones; no crea retroactivamente el ingreso. Mantener movimientos inmutables con compensaciones, importes exactos y cuenta/moneda/origen.

Para un abono sin reversas externas, cada céntimo ocupa una sola categoría: aplicado a compras, pendiente sin aplicar, reservado para devolución, efectivamente devuelto o saldo de vale vigente si se acepta esa función. Reclasificar no crea ingreso. Canjear un vale transfiere saldo hacia una compra; no cuenta simultáneamente como reembolso. Una reversa/contracargo externo posterior requiere asiento y diferencia/obligación correspondiente, no borrar una venta histórica.

Ejemplo de devolución parcial: venta S/10 y retorno autorizado S/4 → liberar/reclasificar S/4 de aplicación a obligación; venta neta/aplicación remanente S/6, obligación S/4. No exigir anular toda la venta para que aparezca saldo. Mantener motivo y relación con líneas/stock devuelto según política, sin confundir devolución monetaria con reingreso automático de mercadería.

Reserva S/7 sobre obligación S/10 deja S/3 disponibles. Un timeout conserva esos S/7 reservados; otra solicitud S/7 se bloquea. Consultar/reconciliar antes de liberar. Un reintento usa la misma identidad idempotente; volver a enviar la solicitud no demuestra que la anterior no se ejecutó. Reservar también saldo contable de caja si ese es el medio. No mantener una transacción de base de datos abierta durante una llamada bancaria.

Los `CheckConstraint` de importes y los locks ayudan, pero contadores almacenados deben corresponder a sus movimientos. Un check de columnas no demuestra sumas de filas hijas. Hacen falta transacciones, unicidad de identidad externa, conciliación y pruebas reales de concurrencia en la base prevista. Nada de esto está implementado por figurar aquí.

## 4. Riesgos que A′ controla y los que permanecen

| Amenaza | Control propuesto | Residual |
|---|---|---|
| Captura falsa, callback inventado o ID nuevo falso | Evidencia autenticada y validación de cuenta, ambiente, moneda, importe, estado e intento; unicidad adicional | Compromiso del proveedor/servidor; cajero aún puede entregar bienes físicamente |
| Repetición o avisos indistinguibles | Persistir eventos; identidad externa estable; consulta/reconciliación; cuarentena sin eliminar evidencia | Notificación sin identidad suficiente puede requerir excepción; no prometer plena automatización con ella |
| Cajero reclama abono ajeno | Relación externa con intento emitido antes del pago; no selección libre del abono por vendedor | Colusión fuera del sistema y pagos sin referencia necesitan tratamiento aparte |
| QR sustituido | Receptor configurado por administración, QR generado para intento y vista controlada | QR físico ajeno o equipo/browser comprometido; no existe control absoluto del mostrador |
| Pago del QR anterior y del nuevo | Reservar exposición hasta cierre externo concluyente | Carreras o QR no cancelable; requiere ruta de reintegro |
| Dos reintegros concurrentes/timeout | Reserva monetaria y de caja, idempotencia y reconciliación | Error operativo de efectivo, actor privilegiado o proveedor pueden requerir investigación |
| Saldo contable distinto del físico | Registro de entradas/salidas, reservas, conteos y diferencias | Billetes faltantes y denominaciones no se miden con SQL |
| Teléfono/servidor sin red o sin avisos | Estados desconocidos, consultas y conciliación, pedido aparcado | Tiempo de atención mayor; no volver a cobrar para ocultar incertidumbre |

Un listener Android puede aportar evidencia legítima bajo custodia y permisos adecuados, pero [NotificationListenerService](https://developer.android.com/reference/android/service/notification/NotificationListenerService) no certifica identidad bancaria. HMAC prueba origen del canal del teléfono, no una firma bancaria. El [código de tres dígitos documentado por Yape](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/como-puedo-yapear-a-alguien-que-no-esta-en-mis-contactos) no demuestra unicidad universal ni referencia de pedido. Se conserva el análisis por capas del dictamen principal; no se acepta el adaptador EMVCo artesanal como equivalente al QR oficial sin ensayarlo y verificar uso permitido.

## 5. Prueba decisiva y orden de construcción

**G0 documental/comercial, PD:** obtener respuesta para una sola combinación: persona natural propia con DNI/sin RUC, uso declarado de demo, SDK Web `QR` productivo, cuenta de abono, tarifa completa/mínimos, billeteras admitidas, importe inmodificable, referencia consultable, cancelación/expiración y reintegro total/parcial de ese QR. Preguntar qué ocurre tras timeout y qué saldo financia el reintegro. El cuestionario preparado en `PARA-ARGON-Y-VALIDACION-PROVEEDOR.md` sigue sin enviarse. La API general y la afiliación de otro producto no satisfacen G0.

**G1 de cuenta/dispositivo, PD y ejecución futura autorizada:** POS en URL pública HTTPS, subdominio válido del alojamiento si es aceptado; cuenta receptora autorizada, Galaxy indicado y teléfonos pagadores propios/autorizados. Sin comprar dominio por presunción. Registrar versión de apps, payloads sanitizados, IDs, receptor, importe, tiempos de autorización/recepción/transporte/proceso/vista, saldo y resultado de reintegro. Nunca capturar claves/OTP.

Procedimiento mínimo preparado:

1. Venta S/15: fijar aporte QR S/10; escanear en cada billetera que se vaya a anunciar. Verificar receptor e imposibilidad de cambiar importe. Completar con S/5 en efectivo y verificar asiento de caja por S/5.
2. Venta S/10: aportes S/3 + S/7 desde personas distintas. Comprobar dos abonos, una venta, stock una vez y trazabilidad por origen.
3. Dos pedidos con igual importe: pagar uno; el otro no cambia. Repetir notificación y consulta sin segundo ingreso. Las inyecciones adversas son pruebas técnicas aisladas, no transferencias falsas al proveedor.
4. Sustituir/cancelar QR en entorno permitido: documentar respuesta y si sigue pagable. Si no hay cierre concluyente, el sistema mantiene reserva y no ofrece reemplazo libre.
5. Reintegro parcial y total sobre pagos distintos ya realizados, con autorización específica y fondos previstos: verificar destino y estados reales. Probar timeout de integración de manera aislada y demostrar recuperación sin segunda devolución. No generar transferencias ni falta deliberada de fondos sin autorización.

Estos casos no son un presupuesto cerrado: los importes anteriores incluyen S/20 digitales y S/5 de efectivo; los demás casos y reembolsos deben enumerarse antes de financiar el ensayo. No prometer una demo por S/10 ni latencia de un segundo. Una muestra pequeña mide esos casos, no disponibilidad poblacional ni un SLA p95 confiable.

**Continuar:** G0 compatible, importes/receptor/referencia comprobados, ninguna doble aplicación, ruta de reintegro operable y política aceptada. **Cambiar/abandonar:** producto niega acceso sin RUC, QR no cumple las billeteras/importe exigidos, no hay evidencia autenticada asociable, o la devolución indispensable no puede financiarse/ejecutarse. No sustituirlo silenciosamente por vale, QR URL o validación por importe.

**Construcción tras aceptar cambios de planificación:** primer incremento = pedido durable + intentos/saldos/aplicaciones + recuperación idempotente + desglose de efectivo. Termina con casos monetarios y concurrencia en PostgreSQL, stock una vez, errores recuperables y trazabilidad HU/CA/CP; proveedor simulado solo para esas pruebas. Esto es independiente del canal. El adaptador productivo, credenciales, permisos reales de devolución y promesas de QR quedan después de G0/G1. Antes de dinero real: autorización de cuenta y participantes, política de devolución financiada, HTTPS/persistencia, segregación de permisos, logs sin secretos, conciliación y ensayo acotado registrado. No hubo aquí publicación ni ejecución bancaria.

## 6. Cambios sugeridos para planificación, sin incorporarlos

Estos identificadores son **provisionales**, no numeración aceptada de 08. Cada botón, mensaje, validación y permiso se documentará en la HU indicada antes de desarrollarlo. No generar vistas 07/09/03 desde esta propuesta.

| Referencia existente / propuesta | CA provisional | CP provisional y resultado observable |
|---|---|---|
| HU-VEN-10, CA de reparto/efectivo | CA-PROP-A01: distinguir propuesto/recibido/aplicado/devuelto | CP-PROP-A01: S/15 digital + S/5 efectivo ya recibido conserva deuda S/5; si efectivo pendiente, queda cero pendiente |
| HU-VEN-10, varios aportes | CA-PROP-A02: importe por intento y exposición reservada | CP-PROP-A02: QR15 no cerrado impide nuevo QR10 contra mismo saldo; pago tardío conserva pedido |
| HU-VEN-06a/b/c | CA-PROP-A03: obligación y beneficiarios por origen, retorno parcial | CP-PROP-A03: cancelación tras S/3 conserva S/3; retorno S/4 sobre venta10 conserva remanente6 |
| HU-VEN-06a/b/c | CA-PROP-A04: reserva persistente de reintegro | CP-PROP-A04: dos solicitudes7 sobre10 y timeout no permiten salida14 |
| HU-CAJA aplicable + HU-VEN-10 | CA-PROP-A05: saldo contable/reservas separado de conteo físico | CP-PROP-A05: caja contable20, física5, solicitud10 no se declara entregada; incidencia y responsable visibles |
| HU-VEN-06a/b/c | CA-PROP-A06: falta de canal = pendiente, no «reintegrado» | CP-PROP-A06: caja0 y QR sin refund no emite éxito; muestra obligación; vale no se impone |
| HU-VEN-02a y RN-13/RN-26 | CA-PROP-A07: documentos internos distinguen venta/deuda/entrega | CP-PROP-A07: leyenda interna vigente; deuda no muestra dinero devuelto ni condición fiscal |
| Permisos de usuarios existentes, ampliación por acordar | CA-PROP-A08: permiso delegado para excepciones, sin autoaprobación | CP-PROP-A08: VENDEDOR no acredita por afirmación ni aprueba su devolución; delegado limitado y auditado |
| Integración propuesta | CA-PROP-A09: autenticidad más unicidad y cuarentena | CP-PROP-A09: ID nuevo falso rechazado; colisión de atributos no borra ni acredita aviso sin evidencia suficiente |
| Recuperación propuesta | CA-PROP-A10: consulta/aparcado y mensaje de incertidumbre | CP-PROP-A10: fallo tras pago completo no produce segunda venta, segundo stock ni cobro adicional |

02 debe describir límites de confianza, exposición de intentos, persistencia de avisos y movimientos, bloqueo/transacciones breves, conciliación y recuperación. 16 debe dividir modelo monetario, pruebas, caja, permisos, interfaz y un adaptador condicionado; no fijar número de migración ni librería como si estuvieran implementados. La integración de pagos y ampliación de permisos requieren planificación futura, sin reabrir Etapas 01/02 por este informe.

## 7. Decisión que permite avanzar

**RECOMENDACIÓN:** A′ y un canal oficial QR por importe/intento; comprobar Izipay primero. Mantener RN-13/RN-26. Descartar la aprobación global de A y la obligatoriedad de vales.

**CONDICIONES PENDIENTES:** habilitación exacta DNI/SDK, comportamiento real QR/reintegro y política financiada para excepciones. Si se necesita devolución inmediata incluso con caja vacía, esa capacidad es criterio de selección, no una mejora opcional.

**QUÉ PODEMOS CONSTRUIR YA:** concretar y aceptar las HU/CA/CP del núcleo monetario; después implementar pedido durable, aplicaciones, caja y recuperación con pruebas aisladas. Esta revisión entrega propuestas listas para decidir, no autorización para modificar requisitos por cuenta del revisor.

**QUÉ TODAVÍA NO PUEDE HABILITARSE:** acreditación real por listener/ID sin garantías del canal, reemplazo libre de QR todavía pagable, reintegros automáticos no comprobados, salidas de efectivo o vales no aceptados, ni actualización de 08 que etiquete A como decisión del usuario.

**Comprobaciones propias:** siete contraejemplos en memoria pasaron. Demuestran fallos posibles en reglas propuestas, no que esos fallos hayan ocurrido en el producto ni su frecuencia. No se ejecutó Django, no se abrió la base operativa, no se hicieron transferencias/afiliaciones/publicaciones. La validación por hashes se registra en `evidencias/OPCION-A-20261115/validacion.json`.
