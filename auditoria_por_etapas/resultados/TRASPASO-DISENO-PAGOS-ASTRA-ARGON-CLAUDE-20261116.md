# Traspaso autocontenido — Diseño de pagos del minimarket

**Corte: 16 de noviembre de 2026, America/Lima.**

**Destinatarios:** Claude sin acceso al proyecto y un nuevo chat encargado de actualizar los prompts de auditoría por etapas.

**Estado:** PROPUESTO — diseño recomendado y criterios consolidados mediante contraste entre GPT Astra y los textos de Gemini Argón compartidos por el usuario. No equivale a aceptación comercial, implementación ni validación bancaria.

Este documento se puede leer y revisar sin los archivos del proyecto. Reúne el resultado vigente; no exige reconstruir las sucesivas respuestas de la conversación. Las referencias locales sirven para localizar evidencia si el siguiente chat sí tiene acceso. Las fuentes públicas están enlazadas directamente. No hubo comunicación directa entre los modelos: el usuario trasladó las respuestas de Argón a Astra.

## 1. Decisión práctica y límites de autoridad

**Recomendación técnica convergente:** Opción A′ corregida + regla R2 corregida + modalidad M2 corregida; constancias internas bajo RN-13/RN-26; sin vales canjeables en el primer incremento. Primer candidato a comprobar: **Izipay SDK Web QR**, por su modalidad exacta, con DNI y sin RUC. Primero consulta de elegibilidad; después, si corresponde y se autoriza, afiliación/ensayo. El puente Android no es un respaldo equivalente ya validado.

El núcleo monetario puede especificarse y, tras aprobación, construirse con un simulador del proveedor. Esto no sustituye la demostración posterior con transferencias reales. Para dinero real falta comprobar conjuntamente acceso de cuenta, QR por importe/intento, evidencia del abono y una devolución autorizada y financiada incluso si la caja está vacía.

**Autorización actual:** investigación, revisión, propuestas y creación de este archivo de traspaso. No se ha autorizado por el mero intercambio de propuestas la edición de requisitos aceptados, integración de pagos, programación del núcleo, afiliación, transferencias, contacto externo ni publicación. La autorización de crear este archivo no autoriza actualizar los prompts ahora: sirve de insumo para el nuevo chat que reciba ese encargo.

En el nuevo chat deben respetarse autorizaciones explícitas adicionales que el responsable otorgue, sin volver a solicitar lo ya autorizado. Una recomendación de un modelo, un texto pegado que pregunta si se aprueba o el consenso entre revisores no son aceptación del responsable.

### Estados y evidencia

- **PROPUESTO:** diseño o política pendiente de aceptación.
- **ACEPTADO:** decisión expresa del responsable, con alcance y fecha identificables.
- **IMPLEMENTADO:** código existente, localizado y contrastado; no basta describir clases.
- **PROBADO:** ejecución real con entorno, casos, resultados y límites identificados.
- **VERIFICADO DOCUMENTALMENTE:** fuente primaria o archivo inspeccionado. Leer código no prueba su ejecución.
- **INFERIDO:** razonamiento de arquitectura, matemático u operativo.
- **PENDIENTE DE DISPOSITIVO O CUENTA:** exige ensayo o confirmación del proveedor/cuenta.
- **DECISIÓN DE NEGOCIO:** facultades, límites, medios alternativos o compromisos todavía por aceptar.

## 2. Contexto y restricciones vigentes

Proyecto universitario: el profesor representa al dueño de un minimarket y evalúa funcionamiento y correspondencia exacta con planificación Scrum. Se exige URL pública HTTPS; no depender de localhost. No hay dominio comprado, servidor contratado ni empresa real; no presumir que se deben comprar. Un subdominio del alojamiento es admisible como posibilidad, sujeto a verificación técnica y del proveedor.

El cajero usa una computadora con el sistema de ventas y gira la pantalla para mostrar el QR. El cliente escanea **dentro de Yape o Plin**. No prometer compatibilidad con cualquier billetera sin lista probada. El importe debe quedar fijado por el aporte, sin que el comprador pueda alterarlo. QR con enlace que abre navegador no es equivalente a ese requisito.

Se deben admitir efectivo, digital, mixtos y varios aportes de distintos teléfonos para la misma compra. La automatización es prioridad; no se acepta como operación ordinaria contratar a otra persona para comprobar cada venta. El dueño no estará disponible para aprobar cada cobro.

Cuenta receptora propia autorizada para el proyecto, nunca la cuenta personal del cajero. No usar identidad, RUC o cuentas de familiares como supuesto. No hay RUC ni afiliación comercial confirmada.

El usuario dispone de Galaxy A52s 5G, Android 14, One UI 6.1, y declara tener Yape con DNI y otra cuenta con BCP. Son datos declarados, no dispositivos/cuentas inspeccionados. No se presume funcionamiento simultáneo de ambas cuentas en el teléfono ni elegibilidad de comercio por tenerlas.

### Cambios de restricciones que no deben perderse

| Tema | Estado vigente en la conversación |
|---|---|
| Cero comisión | Restricción original relajada: el usuario **aceptó evaluar comisión de cobro**. No aceptó una tarifa/proveedor específico |
| Yape Empresa/Ayudantes | Descartado originalmente por comisión. La nueva autorización permite comparar costos, pero no lo convierte en API, QR de importe obligatorio o solución recomendada |
| Devoluciones mediante nuevos yapeos | Prohibición original **sin revocación explícita**. No confundir aceptación de comisión con permiso de transferir para devolver |
| Efectivo para devolver | Aceptó **evaluar** controles y delegación. No es permiso operativo general ni aprobación de límites |
| Segundo empleado | No para verificar cada venta. M2 propone intervención de un ALMACENERO ya existente solo en excepciones de devolución |
| Fiscalidad | Conservar constancia interna; no ampliar a SUNAT. La descripción coloquial «boleta/factura» no autorizó integración fiscal |
| A′, R2, M2 | Recomendación convergente, todavía **PROPUESTA**, no incorporada como aceptada en 08 |
| Topes de M2 | Última propuesta de Astra: S/15, S/15 y S/30 para demo; **no aceptados** y sin posterior validación expresa de Argón |

Separar comisión de cobro de teléfono, conectividad, hosting, mantenimiento, licencias y comisiones de reintegro. No presentar una solución como completamente gratuita por no cobrar porcentaje de recepción.

## 3. Línea base del proyecto y evidencia disponible

Workspace original: `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/`.

| Fuente | SHA-256 de referencia |
|---|---|
| `08_Historias_de_Usuario.md` | `c0aa262b2dceba783ffa08e61bcca985857d777f5ef38be7749c4dd99d47e632` |
| `07_Reglas_de_Negocio.md` | `04b4eae110b96125bb6c91462818883ca1655638c088094c1115cee92a14ea4c` |
| `21_Alcance_Actual_y_Diferencias.md` | `52daf4a562991ca9327b3859021b03f92c3477d086c91cee5c18cbe4da1d1eee` |
| `r1-pmv.zip` | `03145af8aa1063e62b37c6d4736413ad306cd05ce971914fc44df61bfd40522d` — referencia aportada por Argón; **no recalculada para este traspaso** |

Astra inspeccionó el árbol real `r1-pmv`, no dedujo su estado del ZIP. HEAD observado: `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, con cambios locales preexistentes. Manifiesto de 232 archivos seleccionados de producto: `6fec70fa58a357f7b679656d29ec722daff62b495da075c995869c3db0214fea`. HEAD solo no identifica esos cambios. Los hashes de 08/07/21 se recalcularon durante la revisión; el nuevo agente debe volver a comprobarlos si necesita editar.

### Qué existe y qué no debe presumirse

Inspección documental del código:

- Tres roles existentes: administrador (`ADMIN` en documentación), ALMACENERO y VENDEDOR. No agregar cuarto rol por comodidad; permisos delegados son una ampliación a especificar.
- Ventas: `SaleCounter`, `SaleDraft`, `SaleDraftLine`, `Sale`, `SaleLine`, `SaleLotAllocation`. La función de cobro inspeccionada es `checkout_sale` en `sales/services.py`, no asumir que se llama `confirm_sale` por aparecer así en textos previos.
- Cobro actual principalmente en efectivo: valida recibido contra total, calcula vuelto, verifica precio/stock y confirma venta con asignación de lotes. El borrador actual no es automáticamente el pedido durable del nuevo diseño; su descarte puede borrar líneas.
- Caja: configuración de caja única y turno abierto global en el corte; el cierre inspeccionado calcula esperado como apertura más ventas. Esto **no sirve sin cambios** para sumar todos los totales de ventas mixtas como efectivo.
- Locks de checkout incluyen actor, registro de caja, turno y después borrador/líneas/productos y otros recursos; cierre bloquea actor/turno. No fijar otro orden aislado como garantía universal.
- No existen por esta propuesta los modelos de intentos digitales, créditos, reintegros ni sus permisos. Los nombres siguientes son de diseño, no migraciones aprobadas.

Pruebas monetarias de la revisión: modelos aislados en memoria para contraejemplos y aritmética. No son pruebas de Django, PostgreSQL, billeteras ni transferencias. Las pruebas históricas de otras auditorías conservan su build y alcance; no validan entidades nuevas. No se realizaron afiliaciones, transferencias o despliegues durante esta revisión.

## 4. Selección del canal y conclusiones documentales

| Alternativa | Valor y limitación | Decisión vigente |
|---|---|---|
| Izipay SDK Web `QR` | Documenta QR interoperable en SDK Web; afiliación con DNI aparece en oferta general. No se ha demostrado que la combinación exacta sea productiva para este usuario ni que admita reintegro QR | Primer candidato a consulta y ensayo; **no seleccionado productivamente** |
| Mercado Pago Checkout con Yape | Flujo documentado mediante celular y código de autorización; reembolsos documentados sujetos a saldo. Tarifa pública consultada de checkout inmediato: 3,49% + S/1 por operación | Alternativa condicionada a cambio de experiencia aceptado; no equivalente al escaneo dentro de Yape/Plin |
| QR receptor + puente Android | Avisos pueden aportar evidencia legítima, con custodia y transporte seguro. No prueban por sí solos importe obligatorio, referencia inequívoca ni devolución | Investigación secundaria; no respaldo automático equivalente |

Conclusiones que deben preservarse:

- Izipay: no afirmar «todo exige RUC» ni «tener DNI garantiza SDK QR». `QR` figura para SDK Web; `YAPE_CODE` figura para todos los SDK en la tabla consultada. No confundir productos.
- PDF Izipay v307: restricciones QR localizadas en p.12 PPTR y p.33 APP Izipay. El alcance exacto de SDK Web sigue pendiente. Pp.45–46: tramo de facturación/licencia Ari, no prohibición de cobrar más de S/20.000. P.66: restricción de comercio electrónico de Google Pay, no exclusión general de DNI. P.102: inicio de campaña, no fecha global del contrato.
- No inferir de estos contratos que todo QR del Perú carece de devolución automática.
- Mercado Pago: el cargo fijo importa en varios abonos. Para S/10, fórmula agregada de uno/dos/seis cobros da S/1,349, S/2,349 y S/6,349 antes de reglas efectivas. Redondeo por operación puede diferir; no afirmar netos ni IGV definitivo sin tarifa aplicable comprobada. La API de devolución no crea liquidez.
- HMAC del Android autentica el canal del dispositivo, no una firma bancaria. ID local, código corto Yape, nombre e importe no son identificadores bancarios universalmente únicos.
- Android puede repetir, actualizar o agrupar avisos. No descartar pagos por coincidir en 15 segundos ni dar por nuevos los repetidos fuera de 180 segundos o al cambiar turno.
- No automatizar banca por accesibilidad, compartir claves, capturar secretos o evadir protecciones. El uso permitido del canal debe comprobarse.

## 5. Modelo monetario propuesto

Los siguientes son conceptos; el diseño final puede unificarlos sin perder semántica. No obligan a crear una tabla por nombre.

| Concepto | Responsabilidad |
|---|---|
| Pedido durable | Snapshot de líneas/precios/descuentos, total y versión; persiste antes de exponer cobro. Puede ser evolución de SaleDraft o entidad distinta |
| PaymentAttempt | Intento por un aporte concreto, receptor esperado, importe, moneda, referencia de pedido y estado externo |
| Evento/aviso | Evidencia original sanitizada y trazable; distinto del dinero y de su aplicación |
| PaymentCreditRecord | Abono comprobado con identidad externa en su ámbito, importe y cuenta; persiste aunque no exista venta |
| Aplicación de dinero | Vincula cantidad de un crédito/aporte al pedido y, después, venta; no duplica ingreso |
| SalePaymentAllocation | Nombre provisional del detalle de aportes aplicado a la venta; conservar vínculos previos del pedido |
| Sale | Compra confirmada una vez, con stock y aplicaciones consistentes |
| ProductReturn | Solicitud/autorización por línea, cantidad y precio neto original; destino físico separado de dinero |
| Obligación de reintegro | Deuda reconocida por exceso, cancelación o devolución; admite casos sin Sale |
| RefundAllocationLine / RefundExecution | Imputación por origen, reserva, intento de ejecución y resultado individual |
| Movimiento de caja | Entrada/salida física, vuelto y ajustes, asociados al turno de ejecución |
| Ajuste/conciliación externa | Diferencias, devoluciones de panel, reversas o contracargos sin inventar autorizaciones históricas |

### Estados y conservación

Pedido: preparación, cobro abierto, parcial, cubierto pendiente de confirmación, vendido; aparcado/cancelado con saldo cuando corresponda. Cancelar no borra abonos ni significa devolver.

Intento: creado/expuesto/procesando, confirmado/rechazado/expirado según proveedor; resultado desconocido y cancelación solicitada son explícitos. Ocultar QR o expirar temporizador local no invalida el QR externo.

Crédito: mantener categorías disjuntas, importes exactos y movimientos auditables. Conceptos propuestos: `unallocated_credit`, `allocated_to_open_draft`, `allocated_to_active_sale`, `pending_refund_obligation`, `reserved_in_flight_refund`, `executed_monetary_refund`.

Mover dinero resta de origen y suma en destino, sin doble conteo. La obligación local aún no liquidada suma pendiente + reservado; en timeout el reservado podría estar pagado externamente y debe mostrarse «En verificación con el proveedor». La igualdad contable del crédito necesita considerar ajustes externos; no afirmar que seis acumuladores cubren solos cualquier reversa/contracargo.

Para efectivo, conservar recibido, vuelto debido y vuelto realmente entregado. Si recibido5 y vuelto entregado1, aporte neto4. Un vuelto no entregado es obligación, no reducción ficticia del dinero recibido. Los totales en Sale pueden ser resúmenes derivados; nunca la única evidencia de varios pagos.

## 6. Flujo de cobro y varios teléfonos

1. Preparar pedido durable; congelar versión de precios/descuentos y definir política de stock antes de cobrar. Recomendación: reservar stock por plazo explícito y comprobar vigencia; no mantener locks esperando al cliente. La reserva/expiración todavía requiere especificación aceptada.
2. Elegir importe del aporte digital antes de generar QR. Servidor valida receptor, moneda e importe, no el navegador del vendedor.
3. Crear intento vinculado al pedido y obtener QR oficial. Cliente verifica receptor y autoriza en su propia billetera. No solicitar OTP al cajero.
4. Recibir evento/consultar proveedor con autenticidad verificable; validar comercio/cuenta, ambiente, moneda, importe, identidad y vínculo al intento.
5. Guardar crédito y aplicación una sola vez. Varios pagos producen varios aportes, no ventas duplicadas.
6. Registrar efectivo neto y vuelto. Confirmar venta/stock una sola vez cuando se cubra exactamente el total y se cumplan condiciones.
7. Ante incertidumbre, aparcar pedido, consultar/reconciliar y atender otro. No entregar bienes pendientes ni pedir otro pago de una obligación posiblemente cubierta.

### Ejemplo principal: venta V-1042 por S/15

| Aporte | Importe | Vínculo persistido | Origen |
|---|---:|---|---|
| ALLOC-01 | S/5 | Pedido → ATT-01 → TX-A → aplicación | Primer teléfono digital |
| ALLOC-02 | S/6 | Pedido → ATT-02 → TX-B → aplicación | Segundo teléfono digital |
| ALLOC-03 | S/4 netos | Movimiento de caja y turno → aplicación | Billete5, vuelto1 |
| Total | S/15 | Una venta | Dos operaciones digitales y efectivo |

TX-A/TX-B son ejemplos de referencias externas, no campos garantizados del proveedor. No sustituirlos por ObservedEvent local. La relación se establece antes/durante el cobro, no buscando después movimientos con igual importe/hora. Historial muestra los tres aportes, sus operaciones, aplicaciones, reservas y devoluciones. La constancia interna permite localizar la venta; no prueba por sí sola derecho a cobrar un reintegro.

Compra S/10 con S/3 y S/7 desde dos teléfonos sigue el mismo modelo. Un tercero puede pagar legítimamente, pero eso no permite al cajero apropiarse de un abono ajeno ni cambiar su destino de devolución.

### Cambio de reparto y QR viejo

QR15 todavía pagable + QR10 nuevo crean exposición de S/25. `SUPERSEDED_WATCHED` solo vigila. Antes de reemplazar se exige invalidación/expiración externa concluyente o una excepción de riesgo expresamente aceptada y financiada. No liberar la reserva porque el QR salió de pantalla. Un abono tardío se vincula al pedido original, aunque esté cancelado; nunca a la compra siguiente.

## 7. A′: excesos, cancelación y recuperación

| Caso | Resultado requerido |
|---|---|
| Venta15; previsto digital10+efectivo5; llega digital15 y efectivo no recibido | Aplicar15; efectivo pendiente0; ninguna salida de caja |
| Mismo caso, pero ya se recibieron efectivo5 | Conservar ingresos20; venta15 y obligación5. No borrar efectivo ni devolver automáticamente por otro medio |
| Pedido10 vigente recibe15 | Aplicar10; exceso5 pasa de sin aplicar a obligación |
| Ese pedido se cancela antes de entregar bienes | Reclasificar también los10 aplicados: obligación total15, considerando reintegros ya ejecutados y reservas vigentes |
| Pedido10 recibió solo3 y se cancela | Obligación3; preservar pedido, crédito e intentos |
| Pago insuficiente | Pedido parcial, sin venta/entrega como si estuviera cubierto |
| Venta pagada falla técnicamente al confirmar | Cubierto pendiente de confirmación; reintento idempotente. No volver a cobrar. Si imposible completar, obligación según política |
| Precio/stock cambia después de dinero | No mutar silenciosamente lo acordado ni borrar ingreso. Resolver con snapshot/reserva y consentimiento o devolución |
| Pago al receptor equivocado | No acredita al negocio; no entregarlo como si hubiera llegado ni prometer recuperar fondos ajenos |
| No llega notificación pero sí dinero | Consulta/conciliación de cuenta y estado pendiente; ausencia de push no prueba ausencia de abono |

DP-######## identifica una **constancia de obligación pendiente**, no vale ni comprobante fiscal. Debe decir que no acredita devolución ejecutada. Si existe timeout usar estado de verificación, no afirmar que el banco todavía no pagó. No imponer crédito en tienda ni compra adicional. Todo medio alternativo exige política y beneficiario verificado.

**Incompatibilidad abierta:** caja sin efectivo + proveedor sin reintegro original + prohibición de transferencias nuevas impide prometer devolución inmediata. Se requiere canal alternativo/plazo/responsable/fondos aprobados o proveedor compatible. Registrar DP no resuelve esta condición.

## 8. R2: imputación de devoluciones

Recomendación vigente: efectivo original neto con capacidad remanente primero; después aportes digitales en secuencia estable registrada y desempate por ID. Conservar versión de política y plan; reintento reutiliza el plan. Capacidad consumida incluye autorizaciones pendientes/reservas, no solo pagos ejecutados.

No asumir que un producto fue pagado por un teléfono específico. Los aportes financian la compra; la devolución se refiere a línea/cantidad/precio/descuento originales y se imputa según R2. Clasificación física no implica retorno automático a stock vendible: productos defectuosos no deben volver a venderse por registrar un reintegro.

| Sobre venta15 con efectivo4 + digital A5 + B6 | Imputación |
|---|---|
| Devolución3 | Efectivo3; remanentes1+5+6 |
| Después devolución de los12 restantes | Efectivo1 + A5 + B6 |
| Devolución8 sin devoluciones previas | Efectivo4 + A4 |
| Devolución total15 sin devoluciones previas | Efectivo4 + A5 + B6 |

R2 determina el aporte afectado, no crea liquidez, no convierte digital en efectivo y no concede derecho a quien trae la constancia. Reintegration al origen reduce desvíos, sin eliminar fraude/errores. No saltar silenciosamente a otro aporte/canal si falla la ejecución.

### Redondeo físico

El prorrateo obligatorio R1 se retiró como recomendación principal: puede generar microdevoluciones y efectivo de S/0,67. R2 reduce ese problema pero no elimina todos los céntimos. No redondear catálogo ni saldos digitales por esta razón.

**Propuesta comercial pendiente:** obligación de efectivo0,67, entregar0,70 favorable al cliente: principal0,67 contra capacidad del aporte; ajuste0,03 asumido por comercio, separado. Caja debe reservar/registrar0,70. Reintento no duplica ajuste. No atribuir a la circular del BCRP una obligación específica de implementar esta mecánica de reintegros parciales. La política necesita controlar también fraccionamiento abusivo de ajustes.

### Turno anterior

RN-08 restringe actualmente anulación al turno abierto. Se propone ampliar devoluciones posteriores mediante ProductReturn vinculado a Sale histórica; salidas de efectivo se asocian al turno actual al ejecutarse. No reabrir ni mutar CashShiftClose anterior. Recepción física y reintegro digital no requieren por sí solos caja física abierta. No es obligatorio crear tabla separada por tratarse de otro turno.

## 9. M2: permisos propuestos y topes pendientes

M1 (solo ADMIN remoto) no se recomienda como única salida: mantiene dependencia de disponibilidad del dueño. M2 usa un ALMACENERO existente para excepciones ordinarias. No supone otra persona verificando ventas normales. Colusión entre empleados sigue siendo riesgo residual.

| Acción | VENDEDOR | ALMACENERO | ADMIN |
|---|---|---|---|
| Solicitar cancelación/reclamo | Sí | No en matriz propuesta | Sí |
| Calificar destino físico | No | Sí | Sí |
| Autorizar reintegro ordinario | No | Solo permiso delegado explícito, solicitante distinto, R2 y límites | Sí |
| Cambiar canal/beneficiario | No | No | Solo con política, motivo y evidencia; no revoca automáticamente prohibición de nuevos yapeos |
| Registrar entrega de efectivo autorizada | Sí, en su turno abierto | No | Propuesto con turno vigente y facultad explícita; compatibilidad con custodia actual debe especificarse |
| Solicitar ejecución digital autorizada | Sí | No | Sí; no requiere turno físico |

Servidor posee credenciales; el empleado no recibe secretos. La ejecución digital puede dispararse por servicio después de autorización según interfaz aceptada. Falta de delegado mantiene pendiente/escalamiento; no inferir presencia física a partir de login ni inventar turnos de almacenero existentes.

### Triple límite

1. Por solicitud.
2. Acumulado por pedido/venta, conservando identidad al confirmar Sale.
3. Acumulado diario de autorizaciones delegadas del negocio, no reiniciado por turno/usuario.

**Última propuesta de Astra, exclusivamente para demo y aún no aceptada:** S/15 por solicitud, S/15 por pedido/venta y S/30 diarios. Justificación: un ticket del ejemplo y exposición diaria equivalente a dos tickets. No presentarlos como límites acordados entre el usuario y ambos modelos ni como valores apropiados para operación comercial real.

Día calendario America/Lima; sumar todos los delegados; comprobar/consumir límites atómicamente al autorizar, incluyendo salida total y ajustes; reintento no consume otra vez; timeout no libera. Definir explícitamente liberación de una autorización revocada sin ejecución. ADMIN fuera de topes delegados sigue sujeto a capacidad real, destino, disponibilidad e idempotencia. No inventar importes productivos.

## 10. Identidad, estados, concurrencia y conciliación

Identidad externa de pago y de evento son distintas. Unicidad ejemplo: proveedor/ambiente/comercio/ID externo, si ese es su ámbito documentado. Idempotencia persiste entre turnos. No asumir que todos los proveedores firman un ID individual o usan los mismos nombres/estados.

Secuencia conceptual: pendiente → aprobado; después puede haber reintegro parcial/total, reversa o contracargo según contrato. Es un grafo válido, no una cadena universal ni estados inmutables. Un evento antiguo no degrada estado comprobado; una retransmisión no repite el efecto. Datos inmutables contradictorios se aíslan. Avisos ambiguos sin identidad suficiente no acreditan automáticamente. Un número escrito por el cajero o una captura del cliente no sustituyen evidencia autenticada.

Acusar recibo según contrato después de persistencia durable/procesamiento seguro. HTTP200 no prueba acreditación. Si se desacopla recepción/proceso, recuperación debe recoger eventos persistidos no procesados. Evitar datos personales/secretos innecesarios en bitácoras; definir acceso, retención y evidencia de integridad, no declarar inmutabilidad absoluta por nombrar una tabla.

Reserva previa al reintegro: pendiente → reservado; éxito confirmado → ejecutado; fallo concluyente → pendiente; timeout conserva reserva. Dos solicitudes7 sobre saldo10 no pueden reservar14. También proteger cantidades devueltas, capacidades y límites delegados.

Las llamadas externas van fuera de transacciones locales. Acordar orden común de bloqueos entre rutas de caja, pedido, créditos, devolución e inventario; incluir reintegros sin Sale. PostgreSQL con conexiones independientes para concurrencia; SQLite no demuestra locks por fila. Tratar conflictos transitorios identificados con rollback/reintento acotado e idempotente; no reintentar ciegamente toda excepción OperationalError ni resultados de commit/red desconocidos.

Conciliación separa: bruto recibido, aplicado, pendiente, reservado, reintegrado, comisiones/ajustes, liquidación del proveedor y caja. La comisión no reduce lo que el cliente pagó por su compra. Un reintegro desde panel externo no inventa autorización/reserva local previa; registrar hecho externo, vincular origen y revisar diferencias. El rollback de la BD no revierte transferencias.

## 11. Matriz breve de amenazas

| Amenaza | Control propuesto | Riesgo residual |
|---|---|---|
| Capturas/apps falsas | Evidencia del receptor/proveedor autenticada | Cuenta/dispositivo/servidor comprometidos |
| QR de empleado | Receptor configurado con permisos, QR por intento, vista controlada | Sustitución física o equipo manipulado |
| Igual importe, dos cajas, tercero paga | Referencia externa del intento; aplicaciones únicas | Pago sin referencia queda pendiente; no asumir soporte multicaixa actual |
| Avisos duplicados/actualizados/fuera de orden | Identidades persistentes, transiciones válidas, efectos únicos | Canal sin identidad suficiente exige excepción/conciliación |
| Código corto repetido/adivinado | No usarlo como identidad bancaria universal | Colusión y reclamación de abono ajeno |
| Pago tardío de pedido cancelado | Conservar intento/pedido y reconocer saldo | Requiere ruta de devolución operable |
| Móvil sin red, reinicio o permiso revocado | Estado de salud, cola/reintento seguro y conciliación si se usa puente | Abonos sin aviso; latencia no garantizada |
| Servidor cae o se pierde respuesta | Persistencia durable, recuperación idempotente | Incertidumbre temporal; no doble cobro/entrega |
| Doble reintegro/fraccionamiento | Reservas, límites acumulados, permisos y evidencia | Colusión, ADMIN comprometido, entrega fuera del sistema |
| Falta de efectivo | Saldo contable/reservas + comprobación física | Software no cuenta billetes ni impide todo robo físico |

## 12. CA y CP consolidados, identificadores provisionales

Estos CP están **DISEÑADOS, NO EJECUTADOS**. Deben incorporarse a las fichas completas de 08 solo tras aceptación, sin colisionar IDs. Cada variante restaura base aislada salvo secuencias explícitas. Usar cuentas ficticias y simulador determinista, sin dinero real. HTTP403 para permiso denegado; conflictos de negocio deben concretar respuesta/mensaje único antes de aprobar interfaz, no dejar «409/422» como resultado exacto indistinto.

### R2-01 — Reparto y capacidad remanente

**Vínculos:** HU-VEN-10, HU-VEN-06b, HU-VEN-01c.

**Precondiciones:** venta15, productoA12/productoB3; aportes digitalA5, B6 y efectivo4 netos; caja50; política/permiso de prueba definidos.

**Pasos:** calificar y autorizar retornoB3; persistir plan; después autorizar retornoA12 y persistir plan. Repetir la primera petición con la misma clave.

**Esperado:** primer plan efectivo3, remanentes1+5+6; segundo plan1+5+6. Reintento mismo plan, sin duplicar capacidad ni movimientos. Distinguir capacidad autorizada de ejecución real.

### R2-02 — Caja actual y ajuste

**Vínculos:** HU-VEN-06b, HU-CAJA-02/03/04.

**Datos:** A: capacidad histórica4, caja0, devolución3. B: principal0,67 + ajuste0,03, saldo contable0,67. Variante: contable10 y falta física de billetes.

**Pasos:** intentar reservar/ejecutar. **Esperado:** no ejecutado; obligación/solicitud conservada; esperado de caja no baja como si se entregó. B necesita0,70, no0,67. Variante registra incidencia. Saldo contable0,67 es fixture matemático; no afirma que existan monedas para componerlo físicamente.

### R2-03 — Turno original cerrado

**Vínculos:** RN-08/RN-10, HU-VEN-06a/b, HU-CAJA-02/03.

**Precondiciones:** venta histórica, cierre1 esperado104 preservado; plan autorizado de prueba con tramo efectivo3 y tramo digital válido; sin turno abierto. Especificar reparto/orígenes suficientes en el fixture, no presuponerlos por el ID de venta.

**Pasos:** recibir/calificar producto; ejecutar digital en simulador; intentar efectivo sin turno; abrir turno2 con20 y ejecutar efectivo3; intentar editar cierre1.

**Esperado:** actos no efectivos permitidos con sus permisos; efectivo sin turno denegado; turno2 esperado17; cierre1 permanece104 y sin mutaciones. Hash externo de evidencia no presupone un campo de hash ya implementado en el cierre.

### R2-04 — Neto y repetición de entrega

**Vínculos:** HU-VEN-01c, HU-VEN-10, HU-CAJA-03.

**Datos:** venta4, recibido5/vuelto1 entregado; solicitar reintegro5; otra variante autorizada principal0,67+ajuste0,03 con fondos suficientes.

**Pasos:** rechazar5; ejecutar0,70; repetir clave y simular pérdida de respuesta tras registro/entrega. **Esperado:** capacidad4; consumo0,67; salida0,70; ajuste una vez. Si no puede establecerse entrega, conciliación, no segunda orden automática. Registrar límite de la prueba: simulador no demuestra entrega física humana.

### R2-05 — Estados y reintegro externo

**Vínculos:** HU-VEN-10, HU-VEN-01c.

**Datos:** intento5, comercioM1, PEN, TX-A. **Pasos:** pendiente, aprobado, aprobado repetido en otro turno, pendiente viejo. **Esperado:** crédito5 una vez, sin degradación.

**V5 local:** crear autorización/reserva2 antes de evento de reintegro2; confirmar una vez, reservado→ejecutado.

**V5 externa:** sin orden/reserva local, recibir confirmación autenticada de devolución2 desde panel; registrar hecho externo y revisión de conciliación sin inventar aprobación histórica. Preservar crédito bruto5 y devolución2 separados.

**V5 anomalía:** mismo ID con cuenta/moneda/importe inmutable contradictorio; aislar sin acreditar ni alterar silenciosamente. Distinguir principal original de campos de monto devuelto según esquema del proveedor.

### R2-06 — Sin Sale, exceso, timeout y concurrencia

**Vínculos:** HU-VEN-06b, HU-VEN-10, HU-CAJA-02.

**A1:** pedido10 vigente recibe15 → aplicado10, obligación por exceso5 desde saldo sin aplicar.

**A2 secuencial:** cancelar completamente A1 antes de entrega → aplicado0, obligación total15, considerando ejecución/reservas previas. No dejar obligación solo5.

**A3 independiente:** pedido10 recibió3 y cancela → obligación3 sin Sale, sin pérdida de evidencia.

**B:** obligación10; dos conexiones PostgreSQL solicitan7; primera reserva antes de red y queda con timeout → reservado7, pendiente libre3; segunda no reserva7. Consultar/reintentar sin duplicar pago.

**Variantes:** cierre/cobro/devolución concurrentes; conflicto transitorio y recuperación con misma clave; no llamadas HTTP bajo transacción. Registrar versión de PostgreSQL, resultados y límites; no declarar ausencia universal de deadlocks.

### R2-07 — Permisos y acumulados M2

**Vínculos:** RN-09, HU-VEN-06c/06b y permisos de personal a refinar.

**Datos:** vendedor, delegado almacenero y admin distintos; políticas de prueba explícitas. Se pueden usar15/15/30 como fixture sin aceptarlos para operación.

**Pasos:** vendedor solicita e intenta autoautorizar; delegado autoriza ordinaria permitida; solicitudes cruzan límite por operación/venta/día; intenta cambiar medio/beneficiario; ejecutar con/sin turno por medio.

**Esperado:** autoautorización prohibida; autorizaciones válidas registran ambos actores; exceder límites escala/pende sin desembolso; delegado no cambia destino; digital autorizado no exige turno físico; efectivo sí. No confundir login con presencia de delegado.

**Variantes:** dos autorizaciones simultáneas contra último saldo delegado; varios delegados y cambio de turno no reinician día; pedido→Sale conserva acumulado; reintento no consume dos veces; timeout no libera; ADMIN no puede exceder capacidad monetaria aunque no tenga tope delegado.

### Cobertura complementaria obligatoria

Estos siete CP no cubren solos toda la integración. Añadir referencias para QR sustituido/tardío, dos pedidos de igual importe, cuenta incorrecta, pago sin push, stock/precio tras abono, fallo al confirmar venta cubierta, pago3+7, digital5+6+efectivo4, recuperación de eventos persistidos, error de autenticación y entrega física incierta. Cada pantalla/botón/mensaje/validación necesita HU/CA/CP y literal aprobado antes de implementarse.

## 13. Consulta de elegibilidad a Izipay — preparada, NO enviada

Presentación propuesta: proyecto universitario, persona natural propia con DNI y cuenta en soles, sin RUC ni empresa, demostración HTTPS con pagos reales pequeños autorizados; buscar modalidad exacta SDK Web QR. No simular negocio afiliado ni omitir el uso académico. No enviar credenciales ni datos bancarios sensibles en la consulta.

1. **Elegibilidad:** ¿puede esa persona obtener credenciales productivas para SDK Web `payMethod="QR"`, sin RUC, para el uso indicado? Identificar contrato y producto exactos.
2. **Billeteras:** ¿el QR mostrado en computadora es escaneable dentro de Yape y Plin? ¿Qué apps/bancos/versiones están soportados?
3. **Importe:** ¿queda obligado el importe del intento sin edición por el comprador? ¿Sirve para un aporte5 o10 de una compra15?
4. **Referencia y evidencia:** ¿cómo se verifica autenticidad, cuenta, moneda, importe, estado e identidad de operación y su vínculo con referencia de pedido? ¿Qué notificación y consulta servidor-servidor están disponibles?
5. **Vigencia:** ¿cuándo deja realmente de ser pagable? ¿hay cancelación efectiva antes de reemplazar? ¿cómo se resuelven carreras y resultados inciertos?
6. **Devolución QR:** ¿SDK Web QR admite reintegro total/parcial al origen por API o panel, considerando exclusiones contractuales de otros productos QR? ¿Destinatario, estados, tiempos, límites y reconciliación?
7. **Costo y fondos:** porcentaje/cargo fijo/licencia/mantenimiento/IGV, mínimos de cobro y devolución, costo de reintegro, retorno o no de comisión original y fuente de fondos: saldo disponible, ventas no liquidadas o prefondeo.

Conservar respuesta verificable, fecha, modalidad y condiciones. Una respuesta de ventas sobre POS/APP general no prueba SDK. Una consulta externa no es afiliación, pero su envío requiere instrucción explícita; no fue enviado durante esta revisión.

## 14. Ensayo y orden de construcción

**G0 documental/comercial:** respuesta compatible sobre cuenta/producto/QR/referencia/devolución/costos. Si niega requisito indispensable, no construir ese adaptador ni usar fallback incompatible sin decisión.

**Primer incremento del núcleo, tras aceptación:** pedido durable, aportes y aplicaciones, obligaciones/reservas, caja neta, permisos/idempotencia y simulador determinista. Termina con CP pertinentes, PostgreSQL para concurrencia, recuperación y trazabilidad. No terminar solo con tablas creadas.

**G1 de cuenta/dispositivo, ejecución futura autorizada:** URL pública HTTPS, cuenta propia autorizada, credenciales seguras, teléfonos pagadores autorizados, fondos de cobro/reintegro y política. Probar venta15 con digital10+efectivo5; venta10 con3+7; venta15 con5+6+4; referencia frente a dos pedidos iguales; QR viejo; reintegro parcial/total y conciliación. Enumerar operaciones/budget antes: los casos suman más que un único pago pequeño. No realizar transferencias para fabricar fallos sin autorización.

Medir por separado autorización bancaria, recepción del aviso, transporte, procesamiento y acción humana. Muestra pequeña permite aceptar/descartar capacidades de esos casos, no prometer uno/dos segundos o SLA p95 fiable.

**Continuar:** elegibilidad y condiciones compatibles, evidencia autenticada por intento, importe/receptor comprobados, ninguna doble aplicación en casos probados, devolución operable y política aceptada.

**Cambiar candidato/requisito mediante decisión:** no producción con DNI, QR editable/incompatible, sin asociación comprobable, devolución indispensable inexistente o sin fondos. No sustituir silenciosamente por vales, QR URL, nuevos yapeos o afirmación del cajero.

HTTPS sin dominio comprado es posible como diseño; hosting concreto, persistencia, suspensión, PostgreSQL, callbacks, TLS y costos siguen por verificar. No afirmar despliegue público probado por pruebas locales.

## 15. Instrucciones para actualizar los prompts de auditoría por partes

### Autoridad y división que debe conservarse

08 es fuente funcional principal; 07/09/03 son vistas derivadas. 02 es diseño, 14 planificación y 16 tareas; 21 expone alcance/diferencias. Protocolos/prompts e informes no sustituyen aceptación. Actualizar prompts no es actualizar automáticamente requisitos ni producto.

**Etapa01:** ingreso, bloqueo y acceso por rol. **Etapa02:** sesión y gestión de personal. Mantener esta división; no mover cobro/devolución a estas etapas por comodidad. 01-K conserva cierre **solo local de su alcance**. 02-E sigue **PARCIAL**, no cierre global. Cursor general observado: `02-DEMO-TRAZABILIDAD-01`. Consultar el encabezado vigente de ESTADO_GENERAL antes de seguir; los cursores históricos no mandan reiniciar etapas anteriores.

La revisión de pagos no reabre/cierra otras etapas. Las auditorías históricas y sus resultados no se borran ni se convierten en aprobaciones de pagos nuevos. Cada revalidación debe indicar versión de08, build/cambios locales, entorno, roles/casos y alcance exacto.

### Archivos y cambios conceptuales necesarios

| Documento/prompt | Ajuste a preparar cuando el encargo lo autorice |
|---|---|
| PROTOCOLO_COMUN.md | Registrar que evaluar comisiones fue autorizado; separar restricciones originales, propuesta consolidada y cuenta pendiente; preservar procedimiento por sublotes |
| CONTINUIDAD_Y_SEGUNDA_PASADA.md | Actualizar dependencias de pagos sin resetear cursor ni reetiquetar primera/segunda pasada |
| OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md | QR nativo por aporte, multipagador, automatización, devolución financiada y HTTPS real como condiciones; no prometer proveedor |
| PAGOS_YAPE_Y_MIXTOS.md | Sustituir supuestos obsoletos por este diseño como propuesta, con evolución de decisiones trazada |
| 00 línea base | Registrar hashes, autoridad, estados de propuesta y huecos; inventario no es prueba |
| 01/02 | Preservar alcance; solo trazar futura delegación/sesiones con dependencia de implementación, sin cerrar etapas |
| 09 caja | Neto efectivo, entradas/salidas, reservas, ajuste, turno actual y conservación de cierres |
| 10 preparación | Pedido durable, versiones/precios/stock y descarte seguro tras abonos |
| 11 cobro | Intentos/aportes, autenticidad, importe, QR antiguo, mixtos, idempotencia, incertidumbre y confirmación |
| 12 constancias/historial | Pagos individuales/orígenes, DP y ejecuciones parciales; constancia interna no fiscal |
| 13 reportes, 14 integración | No sumar digital a efectivo; bruto/comisiones/neto; recorridos entre tres roles y devoluciones |
| 15 seguridad/despliegue | PostgreSQL, callbacks/reintentos, secretos, permisos, recuperación y HTTPS público; sin datos operativos |
| 16 viabilidad | Producto/país/contrato/tarifa/cuenta, fondos y redondeo; no abrir SUNAT sin aceptación |
| 17 conciliación | Trazabilidad completa, límites de evidencia y dependencias; ningún cierre por documentos o simulador únicamente |

Los títulos/rutas exactos de los prompts deben obtenerse del inventario real. No crear otra numeración de etapas por este mapa. En cada ejecución: proceso acotado y una a tres HU o sublote; inventario bidireccional requisito→interfaz→servidor→persistencia→CP y elemento real→requisito aceptado. Cada texto visible necesita literal/variables/formato aceptados en08 o catálogo referenciado; no basta equivalencia semántica.

Clasificaciones de auditoría: CUMPLE, INCUMPLE, PARCIAL, NO EJECUTADO, NO APLICA con motivo, CONFLICTO DE FUENTES, EXTRA SIN REQUISITO, NO EXAMINADO y PREVISTO/FUTURO. Una función aún propuesta no es automáticamente defecto del producto actual; sí es dependencia pendiente del objetivo final.

**Desfase documental conocido:** protocolos/08 todavía conservan cero comisión en el corte. La conversación autorizó evaluar comisiones. Al actualizar prompts, registrar ese cambio y su procedencia sin falsificar que08 ya se modificó. No borrar los informes anteriores de cero comisión: marcarlos como antecedentes donde corresponda. A′/R2/M2 y topes siguen pendientes de aceptación.

### Encargo listo para un nuevo chat con acceso al proyecto

> Usa este documento como traspaso de contexto y propuesta, no como aceptación de todas sus políticas. Actualiza los prompts de auditoría por partes dentro del alcance que te autorice el usuario. Lee PROTOCOLO_COMUN, CONTINUIDAD_Y_SEGUNDA_PASADA y el encabezado vigente de ESTADO_GENERAL; verifica instrucciones locales, hashes y cambios preexistentes. Conserva01 ingreso/bloqueo/acceso y02 sesión/personal; 01-K local,02 parcial. Incorpora al contexto la autorización de evaluar comisiones y la recomendación A′+R2+M2, distinguiendo pendientes. No modifiques08, vistas derivadas, producto ni estados de cierre salvo autorización específica. Prepara prompts que verifiquen autenticidad/asociación, dinero conservado, devoluciones, permisos, caja/stock y CP descritos. Cada ejecución debe dejar evidencia y siguiente cursor; no simular navegador, PostgreSQL ni banco. Entrega lista de prompts modificados, diferencias, restricciones conservadas y validación de que no cambiaste artefactos fuera del alcance.

### Encargo listo para Claude sin acceso al proyecto

> Revisa independientemente este diseño para un minimarket peruano. No presupongas que está implementado ni que la coincidencia de Astra/Argón lo vuelve correcto. Usa los extractos de contexto aquí incluidos; no afirmes haber leído08 ni código. Prioriza incompatibilidades monetarias, permisos y viabilidad del QR/reintegro; distingue hechos documentales, inferencias y prueba pendiente. No vuelvas a proponer un delegado para cada venta, QR URL como equivalente, nuevos yapeos autorizados por inferencia, ni vales obligatorios. Evalúa A′+R2+M2 y sus CP; informa solo hallazgos accionables con contraejemplo y corrección, sin inventar nuevas aprobaciones. Si faltan datos de proveedor, identifica la pregunta decisiva. No declares completo el ensayo real ni modifiques la autoridad del proyecto mediante tu recomendación.

## 16. Fuentes públicas y procedencia

Referencias usadas durante la revisión de15–16/11/2026; **no se realizó una nueva investigación web completa para redactar este traspaso**. El siguiente revisor debe comprobar vigencia/modalidad antes de contratar o habilitar producción.

1. [Izipay comercial](https://izipayweb.izipay.pe/) — oferta general y DNI no prueban SDK específico.
2. [Izipay Pago con QR](https://developers.izipay.pe/products/pay-with-qr/) y [tabla de valores](https://developers.izipay.pe/value-table/) — producto/método documentado.
3. [Izipay APIs](https://developers.izipay.pe/api/), [notificaciones](https://developers.izipay.pe/notifications/) y [credenciales](https://developers.izipay.pe/credentials/) — comprobar esquema exacto; no asignar campos/algoritmos por inferencia.
4. [Términos Izipay v307](https://cdnwebb.izipay.pe/content-manager/pdfs/terminos/307/terminos) — páginas y límites de interpretación descritos en sección4. PDF inspeccionado de108 páginas, SHA256 `11edfa45f57b53181637a3050490b65626b0542fb087ce87edcf1788116cc0f8`.
5. [Términos QR/PPTR Interbank Negocios](https://interbank.pe/terminos-y-condiciones-para-el-uso-de-codigo-qr-link-de-pago-y-plataforma-de-pago-en-tiempo-real-de-izipay1) — modalidad específica; no extrapolar a todo QR.
6. [Tarifa Checkout Mercado Pago Perú](https://www.mercadopago.com.pe/herramientas-para-vender/check-out), [Yape en Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-api-orders/payment-integration/websites/yape), [reembolsos Checkout Pro Orders](https://www.mercadopago.com.pe/developers/es/docs/checkout-pro-orders/refunds-cancellations) — no mezclar APIs/productos ni tarifa efectiva de una cuenta con oferta general.
7. [Android NotificationListenerService](https://developer.android.com/reference/android/service/notification/NotificationListenerService) — superficie técnica de avisos, no certificación bancaria.
8. [Yape: envío y código de seguridad](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/como-puedo-yapear-a-alguien-que-no-esta-en-mis-contactos) — código no equivale a referencia universal de pedido.
9. [Circular0033-2018-BCRP en El Peruano](https://busquedas.elperuano.pe/dispositivo/NL/1708052-1) — retiro de moneda0,05, canje0,01, redondeo en efectivo y vigencia del céntimo como unidad de cuenta. No sustituye decisión de política específica de reintegro.

Documentos de trabajo locales que este archivo sintetiza: `DICTAMEN-PAGOS-ASTRA.md`, `REVISION-OPCION-A-ARGON-ASTRA.md`, `CASO-PAGOS-MULTIPLES-Y-DEVOLUCION.md`, `REVISION-R2-DEVOLUCIONES-ASTRA.md`, `CIERRE-TECNICO-APROP-R2.md`, `PARA-ARGON-Y-VALIDACION-PROVEEDOR.md`, más los textos posteriores de Argón y respuestas de Astra en esta conversación. Las recomendaciones superadas quedan históricas: delegado en cada venta, R1 obligatorio y descartes generales de proveedores no son la decisión vigente.

## 17. Pendientes exactos y criterio de salida

1. Responsable acepta o ajusta A′/R2/M2, medios/beneficiarios, política de redondeo y topes. S/15–15–30 sigue propuesta de demo.
2. Autoriza actualización controlada de08 y vistas, con fichas/CP/literales completos y cambios de RN-08/permisos explícitos.
3. Autoriza implementación del núcleo separadamente; no se infiere por aprobar documentos.
4. Autoriza envío de consulta externa o la realiza; obtener respuesta verificable de Izipay exacto y condiciones económicas.
5. Resolver devolución cuando falta efectivo: canal, fondos, responsable, plazo y prueba. Si no es compatible, decisión explícita de alternativa/restricción.
6. Ejecutar núcleo aislado, después ensayo público/cuenta autorizado y conciliación; no atribuir pruebas de simulador a banco.

**Resultado utilizable hoy:** diseño consolidado y material de traspaso para revisión independiente/actualización de prompts. **No habilitado:** integración real, reintegros bancarios/efectivo operativos no autorizados, publicación o declaración de cierre global.

Este archivo no requiere otros adjuntos para comprender la recomendación y sus pendientes. Los archivos originales solo son necesarios para comprobar nuevamente el producto, editar planificación o ejecutar auditorías.

## 18. Verificación al generar este traspaso

El 16/11/2026 se compararon **266 archivos protegidos** antes y después de crear este documento: sin cambios. Incluyen planificación principal, vistas, protocolos/prompts inventariados, estado general y selección de archivos de producto. HEAD, estado Git y manifiesto de producto permanecieron iguales. No se abrió la base operativa para consultas ni se ejecutó producto; leer bytes para hash no equivale a probar la aplicación. Se crearon únicamente este traspaso y su evidencia de generación. La comprobación no recalcula el ZIP de Argón ni acredita servicios externos.

## Aclaración posterior del responsable: integración del ciclo anterior

**16/11/2026 — información declarada por el usuario, no inspección del sistema anterior ni prueba de la cuenta.** El compañero gestionó una cuenta Izipay perteneciente a un integrante del grupo. Se realizaron pagos reales mediante un QR en el que, según recuerda el usuario, el cliente ingresaba el monto. El sistema de ventas no recibía confirmaciones automáticas ni sabía si se había pagado: el cliente mostraba la transferencia y el cajero finalizaba manualmente la compra.

**Corrección de procedencia:** ese antecedente no demuestra que se utilizara SDK Web QR, IPN, API, importe obligatorio o validación autenticada. La modalidad exacta sigue sin identificar. Tampoco acredita acceso actual propio/autorizado ni habilitación comercial del proyecto. Se retira cualquier expectativa de reutilizar una integración automática ya comprobada. El requisito nuevo sigue siendo automatizar la comprobación y asociar cada aporte a su pedido; el QR por sí solo no cumple esas dos funciones.

Los documentos llamados boletas/facturas en el ciclo anterior copiaban el formato para demostrar el flujo y **no tenían efecto tributario**, según el responsable. El profesor pide realismo con límites académicos. Esto no autoriza integración SUNAT ni demuestra emisión fiscal. Mantener el alcance de constancia interna RN-13/RN-26 y distinguir claramente cualquier representación académica de un comprobante fiscal, con la leyenda interna aplicable. Si se desea cambiar la pantalla o su denominación, proponerlo en HU/CA/CP antes de implementarlo.

Esta aclaración describe el antecedente; no cambia por sí sola la selección del nuevo canal, la política de devoluciones ni autoriza cambios en 08 o producto.
