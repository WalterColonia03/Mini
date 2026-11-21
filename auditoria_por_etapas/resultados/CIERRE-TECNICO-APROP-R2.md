# Cierre de contraste: A′ + R2 y selección del primer ensayo

Fecha: **16/11/2026, America/Lima**. Estado: **PROPUESTO**. Este documento responde al último bloque de Argón suministrado por el usuario. No registra aceptación del responsable, no autoriza implementación y no modifica 08 ni sus vistas.

**Decisión técnica:** mantener A′ + R2 corregidas, constancia interna RN-13/RN-26 y exclusión de vales del primer incremento. La comparación de políticas está suficientemente resuelta para preparar requisitos; no hace falta volver a abrir la lista completa de alternativas. Sin embargo, el último bloque no debe incorporarse literalmente: sus garantías sobre identidad externa, idempotencia y locks necesitan las precisiones siguientes.

**Primer canal a comprobar: Izipay SDK Web QR.** Primero elegibilidad contractual/técnica de esa modalidad con DNI, uso académico declarado y cuenta propia; no dar por autorizada un alta ni iniciar afiliación. Confirmar también importe obligatorio, vínculo de pedido, consulta de estado, vigencia/cancelación y reintegro total/parcial QR. Después ensayo de cuenta y dispositivo si el responsable autoriza las acciones necesarias. El puente Android queda como investigación secundaria, no respaldo equivalente: no demuestra por sí solo QR de importe fijo, vínculo inequívoco ni devolución al origen. Un resultado negativo de Izipay no habilita automáticamente el puente.

## 1. Comprobaciones de esta pasada

**VERIFICADO DOCUMENTALMENTE local:** lectura de `sales/services.py`, `cash/services.py` y referencias de HU en 08. El checkout actual bloquea actor, registro de caja y turno antes del borrador/líneas/productos; el cierre bloquea actor y turno y calcula esperado como apertura más ventas. No hay medición continua de billetes físicos en estas funciones. No se ejecutaron Django, SQL, dispositivo ni operaciones bancarias. Los argumentos de concurrencia siguientes son **INFERIDOS**, no deadlocks reproducidos.

La comparación documental previa de monedas, Izipay y planificación permanece como evidencia heredada. No se afirma en esta pasada una nueva verificación del ZIP ni una prueba funcional de los modelos propuestos. El código observado usa SaleDraft como borrador que puede descartarse; hacer durable su información tras intentos/abonos requiere una modificación explícita y pruebas, no solo conservar el nombre de clase.

## 2. Correcciones cerradas para la propuesta

### C1. Identidad del pago no es un ID aislado

Un `provider_tx_id` no tiene por qué estar firmado individualmente ni ser un identificador bancario universal. Puede ser el identificador de un recurso de pasarela. Exigir evidencia autenticada conforme al contrato del proveedor, cuenta/comercio, ambiente, moneda, importe, estado e intento correspondiente, además de unicidad en el ámbito realmente definido por el proveedor. Una FK local almacena una relación; no prueba que esa relación sea verdadera.

El reintegro contra la operación original reduce el riesgo de desviar el dinero a un destino elegido por el empleado. No elimina todo riesgo de suplantación, cuenta comprometida, devolución improcedente o error de asociación. Sustituir «sin riesgo de suplantación» por esa afirmación acotada.

### C2. Idempotencia de efectos, no ignorar cambios de estado

Dos mensajes con el mismo ID e importe pueden ser eventos distintos válidos: pendiente → aprobado, aprobado → reintegro parcial, etc., según el proveedor. Guardar evento/estado y actualizar la operación conforme a transiciones verificadas. El efecto de acreditar el principal ocurre una sola vez. La identidad del evento de entrega y la identidad del pago son conceptos distintos.

Caso mínimo: TX-A/S/5 primero pendiente y después aprobado debe pasar de cero a S/5 acreditados. Repetir el aprobado no aumenta a S/10. Recibir después un evento viejo pendiente no debe degradar el estado comprobado. Un importe/moneda/cuenta contradictorios requiere investigación; un cambio de estado legítimo no se manda a cuarentena por ser diferente. Acusar recibo HTTP conforme al contrato después de persistencia durable o procesamiento seguro, sin perder eventos en un fallo posterior. Una respuesta 200 no demuestra éxito monetario.

### C3. Exceso y devolución no siempre salen de una aplicación existente

Los traslados propuestos son correctos cuando existe saldo en la categoría origen. Pero un exceso puede entrar directamente como saldo sin aplicar. Ejemplo: crédito digital15, aplicación admisible10, exceso5: los5 pasan de `unallocated_credit` a obligación, no se descuentan de otros10 correctamente aplicados. Reclasificar solo saldo realmente existente y preservar el vínculo de pedido. No producir acumuladores negativos ni liberar otro aporte por error.

Cuando se autoriza una devolución se consume capacidad para nuevas autorizaciones, aunque el dinero siga pendiente. Distinción visible: «capacidad restante para otra devolución» no equivale a «dinero ya devuelto». La suma pendiente + reservado representa obligación no liquidada localmente; durante un timeout puede estar pagada externamente, pendiente de conciliación. No mostrar como certeza bancaria que el cliente aún no recibió ese tramo.

### C4. Efectivo físico y ejecución incierta

`physical_cash_available` no se vuelve una medición física por existir como campo. Separar saldo contable disponible después de reservas, último conteo/confirmación y entrega registrada. Si faltan billetes, registrar incidencia y no declarar entrega. Un empleado deshonesto aún puede mentir sobre efectivo físico; el software no elimina ese riesgo.

Comprobar y reservar la salida total, incluyendo ajuste: principal0,67 + ajuste0,03 exige disponibilidad0,70. La capacidad del aporte se consume por0,67. Definir cuándo se puede cancelar/reintentar una ejecución antes de entregar billetes y cómo investigar una respuesta perdida después de entregarlos; no autorizar otra entrega solo porque falló la respuesta web. La clave única de ajuste impide duplicar el registro, no impide físicamente que alguien entregue dinero dos veces.

### C5. Política de locks común y ruta sin venta

No fijar en CA que `Sale -> SaleLine -> PaymentCreditRecord -> CashShift` «evita deadlocks» universalmente. El orden existente de checkout es diferente; eso exige diseñar un orden compatible entre todas las rutas y recursos realmente compartidos. La lectura no demuestra por sí sola un deadlock actual. También hay que incluir cierre de turno, aplicación de pagos, cancelación de borrador, devolución de stock y cambios de permisos cuando corresponda.

Una cancelación tras el primer abono puede no tener Sale ni SaleLine. La ruta de reintegro necesita una raíz durable de pedido/crédito para ese caso. El orden basado exclusivamente en Sale no lo cubre. Mantener un orden común entre recursos adquiridos, bloquear cantidades y dinero, revalidar autorizaciones y definir reintentos acotados ante conflicto. Probar con conexiones independientes en PostgreSQL. Ninguna llamada bancaria debe ejecutarse dentro de una transacción local abierta.

### C6. Separar retorno, caja y permisos sin modelos obligatorios prematuros

La devolución posterior al cierre es una ampliación funcional explícita. Puede representarse con ProductReturn vinculado a Sale y con ejecuciones de caja actuales; no es imprescindible introducir otra tabla PostShiftProductReturn solo por ocurrir en otro turno. Esa elección pertenece a arquitectura.

La autorización/recepción del producto y una devolución digital no deben depender automáticamente de tener caja física abierta. La salida de efectivo sí debe vincularse al turno vigente en su ejecución. No reabrir ni mutar cierre histórico. Las diferencias entre permiso para calificar stock y autorizar dinero permanecen expresas.

### C7. Referencias y pruebas realmente trazables

`HU-VEN-01` no es la ficha exacta de cobro: precisar HU-VEN-01c. HU-CAJA-04 describe resumen, no basta para movimientos/reintegros/cierre: vincular además HU-CAJA-03 y HU-CAJA-02 con su refinamiento. Los siete enunciados son una buena matriz de cobertura, pero no sustituyen CP completos con precondiciones, datos, pasos, variantes y resultados por efecto observable.

## 3. Redacción propuesta para cerrar los CA, sin editar 08

Estos textos sustituyen las garantías excesivas del bloque recibido. Identificadores **provisionales**, pendientes de integración y numeración por el responsable.

| CA provisional | Resultado exigido | CP que debe concretarse |
|---|---|---|
| R2-01 | Plan determinista por capacidad remanente: efectivo original neto, luego aportes digitales por secuencia estable; se persiste versión, beneficiario/origen y reservas | Venta15 con4+5+6; devolución3 y después12; reintento no cambia ni duplica el plan |
| R2-02 | Capacidad histórica y disponibilidad actual separadas; falta de efectivo impide declarar ejecución; principal y ajuste se reservan por su salida total | Capacidad4/caja0: pendiente; deuda0,67/ajuste0,03/caja0,67: no ejecutar salida0,70 |
| R2-03 | Retorno de venta de turno cerrado conserva el cierre; efectivo ejecutado se registra en turno actual; autorización o tramo digital no exige turno físico por sí solo | Venta histórica, caja nueva y casos sin caja abierta; comparar cierre original y movimientos nuevos |
| R2-04 | Neto original=recibido-vuelto entregado; ajuste favorable aprobado es independiente, trazable e idempotente | Recibido5/vuelto1: capacidad4; reintento de entrega0,70 no duplica principal0,67 ni ajuste0,03 |
| R2-05 | Eventos auténticos actualizan estados válidos; efectos monetarios son únicos entre turnos; avisos ambiguos sin identidad suficiente no acreditan | Pendiente→aprobado→aprobado repetido→pendiente tardío; principal5 una sola vez; conflicto de cuenta/moneda aislado |
| R2-06 | Reserva atómica por origen y cantidades; resultado incierto no libera capacidad; incluye anticipos sin venta y cierre concurrente | Dos devoluciones7 sobre10; timeout; cancelación con abono3 sin Sale; retorno/cierre concurrentes; pruebas PostgreSQL, sin llamadas bancarias bajo lock |
| R2-07 | Permiso físico no concede permiso monetario; original de pago y beneficiario verificable gobiernan destino; excepciones autorizadas auditadas | ALMACENERO con solo permiso de stock no desembolsa; VENDEDOR no cambia destino; cambio de medio no se deriva de falta de saldo |

Además del caso de producto defectuoso, documentar cancelación sin producto/venta confirmada, exceso y recepción tardía. El listado de entidades no debe excluir la evidencia de proveedor, registro de eventos, movimientos de caja y recuperación necesarios.

## 4. Decisiones para avanzar sin confundir autorizaciones

1. **Requisitos:** aprobar A′ + R2 con C1–C7 y los CA ajustados permite elaborar la revisión controlada de 08, reglas y vistas; no significa que haya pruebas bancarias superadas.
2. **Implementación:** autorizar el primer incremento del núcleo es una decisión separada. Termina con pedido durable, aportes, aplicaciones, obligaciones, reservas, caja/recuperación y pruebas de invariantes y concurrencia; no habilita el adaptador real ni desembolsos.
3. **Proveedor:** priorizar consulta de elegibilidad Izipay SDK Web QR con DNI antes del alta. No confundir aprobación del plan con autorización para afiliación, transferencias o publicación.

**Bloqueo para dinero real que permanece:** debe existir un mecanismo autorizado y financiado de devolución para el caso sin efectivo. DP y R2 no lo proporcionan. Si Izipay no ofrece devolución original compatible, se necesita decisión explícita sobre canal alternativo/plazo/fondos o cambiar de producto/restricción; no se da por resuelto con la bandeja de ADMIN.

El núcleo puede avanzar tras sus aprobaciones; el proveedor no queda elegido productivamente por este informe. No se añaden roles ni se reabren/cierran etapas ajenas.
