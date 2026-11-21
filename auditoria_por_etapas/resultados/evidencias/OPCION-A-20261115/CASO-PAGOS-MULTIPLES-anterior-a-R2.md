# Caso: dos aportes digitales y efectivo, con devolución posterior

Fecha: 15/11/2026, America/Lima. **INFERIDO / PROPUESTO**: diseño de software; no implementación ni prueba bancaria. Complementa el dictamen ASTRA y la propuesta A′. No cambia 08, producto ni etapas. La posibilidad de reembolsar el pago digital original sigue **PENDIENTE DE DISPOSITIVO O CUENTA**; el reparto de devolución es **DECISIÓN DE NEGOCIO**.

## Caso exacto y vínculo desde el cobro

Una venta de S/15 puede recibir S/5 por Yape desde un celular, S/6 por Yape desde otro y S/4 en efectivo. No se registra una sola fila «Yape S/11»: se conservan tres aportes distintos vinculados al mismo pedido y, al confirmarse, a la misma venta.

Identificadores siguientes exclusivamente ilustrativos:

| Venta V-1042 | Medio | Recibido y aplicado | Referencia del origen |
|---|---|---:|---|
| Aporte P-01 | Digital/Yape | S/5,00 | Intento I-01 y operación externa TX-A |
| Aporte P-02 | Digital/Yape | S/6,00 | Intento I-02 y operación externa TX-B |
| Aporte P-03 | Efectivo | S/4,00 | Movimiento de caja C-03 y turno |
| Total | Mixto | S/15,00 | Una venta |

TX-A/TX-B representan identificadores estables del proveedor, si los suministra. No se inventan sustituyéndolos por código corto, UUID local o nombre del pagador. El sistema conserva la cuenta/comercio receptor, ambiente, moneda e identidad externa con unicidad en su ámbito documentado. Si el proveedor no identifica el pagador, no se muestra una identidad supuesta: el vínculo de operación original puede permitir devolver al origen sin conocer su número de teléfono.

Flujo propuesto: crear pedido durable, elegir aporte S/5 y generar su intento/QR oficial; comprobarlo y aplicarlo. Crear segundo intento por S/6 para el segundo teléfono; comprobarlo y aplicarlo. Registrar efectivo neto S/4. Solo entonces confirmar una venta de S/15. El segundo intento cubre otra porción del saldo; no reutiliza la reserva del primero. Ante resultado desconocido, conservar exposición y no emitir un reemplazo que pueda cobrar dos veces la misma porción.

La relación se establece **antes de pagar**: pedido → intento → operación externa autenticada → aplicación de dinero. El historial la consulta después; no necesita adivinar qué yapeos eran de la venta a partir de importe/hora. Un ID nuevo por sí solo tampoco acredita dinero. Con un QR estático y avisos que no contienen referencia suficiente, este vínculo automático no está demostrado y el caso debe quedar pendiente de comprobación, no resolverse con selección libre del cajero.

## Qué muestra el historial

Propuesta de vista «Detalle de venta», sección «Pagos»: aporte, medio, importe aplicado, estado, hora de confirmación, referencia de operación en vista autorizada, referencia de caja cuando corresponda y vínculo a reintegros. Mostrar nombre enmascarado del pagador solo si está disponible legítimamente y es necesario; no exigir DNI/teléfono del pagador para suplir una referencia bancaria inexistente.

Por cada aporte se distinguen: recibido, aplicado vigente, reclasificado a obligación de devolución, reservado en reintegros, devuelto efectivamente y pendiente. Las categorías no se suman dos veces. Mantener también precio y descuento originales de cada línea, para calcular la devolución sin usar el precio actual del producto.

Constancia de venta interna: total S/15, digital S/11 en dos operaciones, efectivo neto S/4 y referencia única de venta. Su detalle autorizado permite localizar las operaciones. No imprimir datos bancarios completos ni convertir el documento en comprobante fiscal. El código de la constancia permite buscar; no demuestra por sí solo derecho a cobrar una devolución.

## Devolución por un producto defectuoso

La autorización de devolución se refiere a línea, cantidad y valor originalmente cobrado, con su descuento. No presumir que el primer Yape pagó el primer producto: salvo acuerdo explícito, los tres aportes financian la compra completa. La decisión sobre mercadería defectuosa/reingreso a stock es distinta del reintegro monetario; no volver a vender automáticamente el producto devuelto.

Ejemplo: se autoriza devolver un producto cuyo valor neto original era S/3. Deben registrarse dos relaciones diferentes:

1. Devolución D-01 → venta V-1042 → línea/cantidad devuelta → S/3 autorizados.
2. Ejecuciones de reintegro de D-01 → aportes de origen P-01/P-02/P-03 → cantidades reservadas/ejecutadas y evidencia.

**Política recomendada para evaluar:** devolución proporcional a los medios/aportes originales, al origen cuando el canal lo permita. Evita que el vendedor elija arbitrariamente a cuál de los dos pagadores favorecer. Para este ejemplo:

| Origen | Participación en venta | Reintegro propuesto por S/3 |
|---|---:|---:|
| P-01 / TX-A | S/5 de S/15 | S/1,00 |
| P-02 / TX-B | S/6 de S/15 | S/1,20 |
| P-03 / caja | S/4 de S/15 | S/0,80 |
| Total | S/15 | S/3,00 |

El reparto proporcional es una propuesta comercial, no una obligación legal afirmada ni una capacidad probada del proveedor. Tiene costo de complejidad y puede necesitar varios reintegros; mínimos/comisiones del proveedor pueden impedir cantidades pequeñas. Antes de aceptarlo hay que comprobar esas condiciones. Una alternativa de menor número de operaciones requeriría otra política explícita que resuelva los derechos de los distintos aportantes; no dejarla al arbitrio del cajero.

Para importes que no dividen exactamente, especificar reparto a céntimos determinista: calcular cuotas, asignar céntimos restantes con desempate estable, guardar el reparto definitivo y respetar capacidad remanente por origen. En devoluciones sucesivas considerar lo ya ejecutado y reservado; una repetición técnica reutiliza el reparto/identidad de la misma solicitud, no genera otro reparto.

En cancelación total sin reintegros previos, los importes de origen serían S/5, S/6 y S/4. Si un reintegro ya está en curso o ejecutado, no se solicita otra vez esa cantidad. Se protege también la cantidad de producto devuelta acumulada contra solicitudes duplicadas/concurrentes.

## Casos que el historial debe distinguir

- Reintegro sobre operación original permitido: solicitarlo contra TX-A/TX-B y confirmar resultado. Es **PD**, no asumirlo disponible en Izipay QR.
- Proveedor no permite reintegro original: conservar origen y obligación. Tener trazabilidad no crea un canal de devolución. Efectivo u otro medio necesita política aprobada y beneficiario verificado; no pagar automáticamente todo a quien trae la constancia si intervinieron terceros.
- Caja insuficiente: la parte en efectivo permanece pendiente; no se marca entregada ni se impone vale.
- Una ejecución termina y otra queda con timeout: devolución global PARCIAL/EN_RESOLUCION, con estado por ejecución. No deshacer la primera ni repetirla para recuperar la segunda.
- Captura de pago o nombre coincidente: no habilita apropiación de una operación ajena ni cambio de beneficiario. VENDEDOR no puede editar identidad externa, receptor o historial confirmado.

## Trazabilidad propuesta y criterio de aceptación

Referencias existentes: HU-VEN-10 (varios aportes/mixtos), HU-VEN-06a/b/c (devolución/cancelación), HU-VEN-02a (constancia), RN-13/RN-26 (alcance interno). CA/CP siguientes **provisionales**, no incorporados:

- CA-PROP-MULTI-01 / CP-PROP-MULTI-01: S/5 + S/6 desde dos teléfonos y S/4 efectivo → tres aportes, una venta S/15 y dos referencias digitales distintas; stock una vez.
- CA-PROP-MULTI-02 / CP-PROP-MULTI-02: abrir historial permite recorrer venta → aportes → operaciones y devolución → ejecuciones → aportes sin buscar coincidencias por importe.
- CA-PROP-MULTI-03 / CP-PROP-MULTI-03: retorno autorizado S/3 conserva línea/precio/descuento original y reparto aceptado; suma de ejecuciones/reservas no supera autorización ni capacidad liberada de cada origen.
- CA-PROP-MULTI-04 / CP-PROP-MULTI-04: timeout de uno de los reintegros no repite los exitosos; dos devoluciones concurrentes no exceden dinero ni cantidad retornable.
- CA-PROP-MULTI-05 / CP-PROP-MULTI-05: QR estático sin asociación inequívoca no se presenta como aporte automáticamente comprobado; se conserva incertidumbre.
- CA-PROP-MULTI-06 / CP-PROP-MULTI-06: canal sin refund/caja insuficiente muestra saldo pendiente por origen, no éxito ficticio; sin datos sensibles innecesarios.

No se ejecutaron estas pruebas. El caso debe añadirse al ensayo real del canal elegido y al plan de pruebas del núcleo monetario después de aceptar sus requisitos.
