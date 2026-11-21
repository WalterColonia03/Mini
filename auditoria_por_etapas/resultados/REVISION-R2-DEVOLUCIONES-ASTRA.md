# Dictamen sobre R2 y nueva revisión de A′

Fecha: 15/11/2026, America/Lima. **PROPUESTO**, sin cambiar 08, vistas, producto ni estados de etapas. Se contrasta el texto pegado por el usuario, no se interpreta la aceptación técnica de Argón como aceptación comercial del responsable.

**Recomendación: sustituir mi recomendación de prorrateo obligatorio por R2 corregida: capacidad original de efectivo primero y después aportes digitales por orden estable, sin cambiar automáticamente el medio de devolución ni el beneficiario.** Mantener A′ como base propuesta, con las correcciones siguientes. No afirmar que todos los escenarios estén cubiertos.

## 1. Qué corrijo de mi propuesta

**VERIFICADO DOCUMENTALMENTE:** la [Circular 0033-2018-BCRP publicada en El Peruano](https://busquedas.elperuano.pe/dispositivo/NL/1708052-1) retiró S/0,05 de circulación desde 2019, contempla el canje de monedas de S/0,01 y remite el redondeo de pagos en efectivo al artículo 44 del Código del Consumidor. Mantiene el céntimo como unidad de cuenta y para pagos no efectivos.

**INFERIDO:** repartir S/2,50 en proporción 5:6:4 puede producir S/0,67 de efectivo. Ese importe no puede entregarse exactamente con las denominaciones circulantes. Mi propuesta anterior contemplaba redondeo contable a céntimos, pero no desarrolló suficientemente esta restricción física. R2 reduce fraccionamiento y cantidad de operaciones: para devolver S/3 con capacidad original de efectivo S/4, permite una sola salida de S/3, si está autorizada y hay dinero físico. Por eso cambio mi recomendación principal.

No obstante, R2 tampoco elimina todo redondeo: precios, descuentos y capacidades remanentes pueden tener céntimos. No se aprueba redondear precios del catálogo ni reducir unilateralmente una obligación de devolución. Como **DECISIÓN DE NEGOCIO propuesta**, ante deuda de efectivo no representable en monedas, evaluar entregar el siguiente múltiplo de S/0,10 favorable al cliente y registrar la diferencia como gasto/ajuste del comercio separado del reintegro imputado al aporte. Ejemplo: obligación S/0,67, entrega S/0,70 = reintegro S/0,67 + ajuste S/0,03. No imputar S/0,70 contra un aporte con capacidad S/0,67 ni alterar el total de deuda original. Esto es una recomendación comercial, no una conclusión de que la circular imponga esta mecánica específica a devoluciones parciales. Evitar múltiples ajustes duplicados por reintento.

La ausencia física del segundo pagador no demuestra que un reintegro original sea imposible: una API que devuelve sobre la operación puede no requerir que esté presente. Debe comprobarse el flujo del proveedor. No usar ese argumento como descarte universal de R1. R1 sigue siendo otra política posible, pero no la propongo como predeterminada para este PMV.

## 2. R2 corregida y operable

**INFERIDO / DECISIÓN DE NEGOCIO, pendiente de aceptación:**

1. Autorizar primero el retorno monetario por línea/cantidad, precio y descuento históricos. Identificar quién puede recibir cada devolución; el comprador, quien pagó efectivo y los pagadores digitales no son necesariamente la misma persona. La regla de reparto no resuelve titularidad.
2. Calcular capacidad remanente de cada aporte considerando aplicaciones vigentes, devoluciones autorizadas ya asignadas, reservas y ejecuciones. No reutilizar el mismo saldo para dos devoluciones.
3. Imputar primero a aportes originales de efectivo; después a aportes digitales en orden estable registrado (por ejemplo secuencia de aplicación al pedido y un ID como desempate). Registrar versión de política y plan definitivo. Una repetición técnica reutiliza el mismo plan.
4. Efectivo original neto es recibido menos vuelto realmente entregado. Billete S/5 con vuelto S/1 no crea capacidad de reintegro S/5: aporta S/4. Conservar recepción y vuelto por separado para caja, sin tratarlos además como ingreso neto completo.
5. Ejecutar cada parte únicamente por un canal permitido: efectivo exige saldo contable después de reservas, disponibilidad física y autorización; digital exige reintegro original soportado y saldo utilizable. FIFO decide qué aporte se afecta, no habilita una API ni transforma Yape en efectivo.
6. Si falta dinero o canal, conservar la línea pendiente. No saltar silenciosamente a otro pagador o cambiar el medio para ocultar el bloqueo. Cualquier excepción requiere política, beneficiario y autorización registrada.
7. Mantener el historial original y registrar reclasificaciones/ejecuciones sin reescribir los pagos recibidos. Conciliar también caja y proveedor.

Ejemplo sin devoluciones previas: venta15, efectivo4, digital A5 y B6. Devolución3 → efectivo3; remanentes efectivo1, A5 y B6. Si después se autoriza devolver los S/12 restantes, el plan es efectivo1 + A5 + B6, no efectivo4 otra vez. Devolución8 en un caso independiente → efectivo4 + A4. Si el efectivo físico disponible es cero, la parte4 queda pendiente; el cobro histórico no prueba disponibilidad actual.

Si dos reclamaciones se tramitan a la vez, los bloqueos y verificaciones deben proteger tanto el dinero como las unidades retornables. Bloquear solamente PaymentCreditRecord no protege por sí mismo SaleLine, otros créditos ni las reservas de caja. Definir orden estable de bloqueo y transacciones cortas; llamadas externas fuera de la transacción. Son diseños pendientes de pruebas reales, no garantías proporcionadas por nombrar SELECT FOR UPDATE.

## 3. Correcciones pendientes del texto nuevo

| Punto | Evaluación | Corrección necesaria |
|---|---|---|
| S/5 físicos recién recibidos pueden devolverse inmediatamente | **INFERIDO, condicionado** | Puede ser viable devolver ese mismo efectivo a quien lo entregó, pero no es una autorización automática. Verificar disponibilidad y política; no confundirlo con disponer de fondos bancarios ajenos |
| Cinco acumuladores disjuntos | **Mejora de diseño; incompleta** | Al reservar, mover pendiente → reservado; al ejecutar, reservado → ejecutado. La obligación total no pagada se consulta como pendiente + reservado. No incrementar reservado dejando la misma suma en pendiente |
| Aplicación solo a ventas confirmadas | **INFERIDO, hueco de estados** | Dinero de un pedido parcialmente pagado todavía debe quedar vinculado/reservado a ese pedido. Usar aplicaciones a pedidos con estado o ampliar el modelo; no dejar crédito libre reutilizable hasta crear Sale |
| Suma exacta al bruto para todos los casos | **INFERIDO, con alcance** | Definir si efectivo representa ingreso neto o bruto con vuelto separado. Reversas/contracargos externos posteriores necesitan asientos/diferencias adicionales; cinco campos no son una prueba de libro monetario completo |
| `provider_tx_id` o `ObservedEvent #81` como referencias equivalentes | **Incorrecta equivalencia** | El aviso local identifica evidencia, no una operación bancaria única ni su vínculo auténtico con pedido. Mantener identidad externa y evidencia separadas; no habilitar aplicación automática por una FK local |
| Deduplicación comparada solo dentro del turno | **INFERIDO, todavía insuficiente** | Un replay al día siguiente queda fuera. Mantener identidad monetaria persistente entre turnos y retención definida; no usar turno como frontera de unicidad |
| Todo aviso repetido debe ir a cuarentena | **Demasiado amplia** | Retransmisión auténtica con ID estable del mismo pago se procesa idempotentemente y no suma dinero. Colisión ambigua sin identidad suficiente va a cuarentena. No bloquear el comercio por cada webhook repetido legítimo |
| Dos números de operación en historial bastan | **Condicionada** | Es evidencia útil solo desde origen confiable, cuenta/fecha/ámbito correctos y mecanismo de verificación autorizado. Números escritos por cajero o capturas del cliente no bastan. Debe conservarse además vínculo con compra |
| Expiración de QR habilita reemplazo | **PD** | Solo expiración efectiva conforme al proveedor; un reloj local no prueba que dejó de ser pagable. Reconocer deuda por doble pago no reemplaza un mecanismo financiado de devolución |
| RN-09 autoriza al ALMACENERO a reintegrar y crea cuarentena | **No acreditada por 08** | RN-09/HU-VEN-06c tratan destino de mercadería; no conceden automáticamente autorización monetaria. Cuarentena y permiso delegado deben especificarse aparte |
| Cliente vuelve meses después y se procesa devolución dentro del sistema | **Cambio de alcance pendiente** | RN-08/HU-VEN-06a restringen anulación al turno abierto. Proponer devolución posterior como operación nueva vinculada a venta histórica y caja actual; no reabrir ni reescribir cierre original |
| S/20.000 es tope acumulado de Ari | **Terminología todavía incorrecta según lectura previa del PDF** | El pasaje corresponde al tramo de facturación que cambia licencia/tarifa, no prueba un máximo de cobro o prohibición de excederlo |

Los totales Yape/efectivo en Sale no son por sí mismos un error: pueden ser resúmenes derivados y conciliados. El error es que sean la única evidencia y no existan aportes/operaciones individuales. Asimismo, Sale puede crearse al confirmar: antes debe existir pedido durable; no exigir una FK a una venta inexistente ni crear ventas confirmadas ficticias para almacenar anticipos.

La constancia DP ayuda a reconocer la obligación, no financia su pago. Sigue pendiente definir canal, responsable, plazo y fondos si se promete devolver sin efectivo y sin reversa. No presentar esta incompatibilidad como resuelta por A′.

## 4. Propuesta concreta para planificación

No se cambia 08. Complementar HU-VEN-10 y HU-VEN-06a/b/c con criterios **provisionales**:

- CA/CP-PROP-R2-01: venta15 con efectivo4 y digitales5+6; devolución3 imputa efectivo3; devolución posterior12 solo consume remanentes1+5+6.
- CA/CP-PROP-R2-02: caja actual0 no permite declarar efectivo entregado aunque aporte histórico sea4; DP conserva pendiente y responsable.
- CA/CP-PROP-R2-03: devolución de venta con turno original cerrado se registra en operación/turno actual conforme a nueva política aceptada, conservando cierre histórico. Refinar RN-08/RN-10 explícitamente.
- CA/CP-PROP-R2-04: aporte de efectivo neto4 tras recibir5 y dar1 no puede reintegrarse por5; ajuste de monedas se registra aparte si se aprueba.
- CA/CP-PROP-R2-05: replay de mismo pago en otro turno no suma; dos avisos indistinguibles sin identidad suficiente quedan pendientes; ID externo autenticado repetido no genera cuarentena innecesaria.
- CA/CP-PROP-R2-06: reserva de reintegro mueve saldo sin duplicarlo; timeout conserva reserva; reclamos concurrentes respetan cantidades, origen y autorización.
- CA/CP-PROP-R2-07: permiso de evaluar producto no implica permiso de liberar dinero. Beneficiario y cualquier cambio de canal quedan auditados.

**Recomendación final:** A′ como base corregida, sin vales y con RN-13/RN-26; R2 corregida como política preferida para evaluar y aceptar. No declarar aceptados proveedor, reembolsos, nuevos permisos ni devoluciones de turnos cerrados por la aceptación técnica de este texto. Se puede preparar la redacción propuesta de HU/CA/CP, pero su incorporación a 08 exige decisión del responsable.

**Evidencia de esta pasada:** lectura de fuentes oficiales de monedas/redondeo y tramos de 08/07. Se releyeron hashes de 08 y 21, coincidentes con los declarados. No se ejecutaron producto, base operativa ni transferencias; los ejemplos son razonamientos, no pruebas funcionales. Los análisis anteriores de Izipay siguen siendo evidencia heredada identificada, no nueva comprobación contractual.
