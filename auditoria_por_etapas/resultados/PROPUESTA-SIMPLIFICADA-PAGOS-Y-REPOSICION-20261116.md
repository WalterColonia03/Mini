# Propuesta simplificada: cobros reales, cancelaciones y reposición de caja

Fecha: 16/11/2026, America/Lima. **PROPUESTO**, contraste del nuevo adjunto compartido por el usuario. No se modifican requisitos aceptados, producto ni etapas. Es una alternativa de alcance reducido al traspaso extenso, no una declaración de que se implementó o aprobó sustituir toda su política.

## Decisión práctica

Sí es razonable reducir el primer incremento a cobro real completo por QR, mixto, varios teléfonos y cancelación con registro del dinero. Recomiendo **un solo adaptador Izipay comprobado**, pedido durable con varios pagos y libro de caja; incorporar solicitud de reposición física como operación distinta de autorizar una devolución. Sin puente Android, vales ni plataforma multicanal en este incremento.

El usuario menciona una integración Izipay de un ciclo anterior. Es el primer recurso a identificar: modalidad, acceso propio autorizado, prueba/producción, comercio y soporte real de QR. No se presume que el comercio pueda reutilizarse ni que haya credenciales productivas disponibles. No enviar secretos. Las capacidades de cuenta siguen pendientes.

La interfaz puede ser sencilla sin eliminar cuatro controles: asociar cada pago al pedido desde antes de cobrar, validar evidencia externa en servidor, evitar doble aplicación y conservar dinero recibido aunque se cancele o falle la venta.

## Alcance mínimo y herramientas

- **Django y PostgreSQL:** pedido, intentos/aportes individuales, estados e idempotencia; transacciones cortas y unicidad externa. Mantener consulta/historial por venta.
- **SDK Web QR del proveedor:** genera el QR de la orden/aporte. Una librería Python que dibuja QR no crea una orden bancaria interoperable.
- **Backend de integración:** credenciales en servidor, notificación y consulta autenticadas conforme a documentación del producto. No asumir HMAC/clave/cadena concretos porque un ejemplo tenga header Signature. Callback JavaScript no acredita dinero.
- **Actualización de pantalla:** polling autenticado al backend mediante fetch/HTMX es suficiente para el PMV; frecuencia propuesta, no promesa de latencia bancaria. WebSockets no son requisito.
- **Simulador aislado:** prueba duplicados, estados fuera de orden, importes falsos y timeouts; no sustituye pagos reales ni se presenta como Yape.

Modelos/conceptos mínimos: pedido durable, intento/pago, aplicación al pedido, movimiento de caja, obligación/ejecución de devolución y solicitud de reposición. Se pueden agrupar tablas con justificación, pero no fundir hechos distintos. No es obligatorio implementar seis acumuladores como columnas si movimientos y consultas consistentes resuelven los mismos invariantes.

## Tres cobros con el mismo mecanismo

| Compra S/15 | Aportes |
|---|---|
| Todo digital | Un intento15, una operación externa |
| Mixto | Efectivo5 y un intento digital10 |
| Dos teléfonos | Intento7,50 y operaciónA; después intento7,50 y operaciónB |
| Combinación permitida | Digital5 + digital6 + efectivo4, sujeto a mínimos reales del proveedor |

El cliente acuerda cuánto pagará digitalmente; el cajero registra ese aporte y el servidor genera QR por importe fijo. No hace falta un QR editable para admitir mixtos. Un intento digital activo por pedido simplifica atención; un intento desconocido no se reemplaza libremente. El QR antiguo debe quedar efectivamente cerrado o conservarse el riesgo pendiente según proveedor.

Historial: pedido/venta → aportes → orden del proveedor → operación externa → devolución, si existe. No buscar yapeos del día por coincidencias de importe. Dos avisos del mismo pago se procesan sin nuevo ingreso. Dos operaciones reales distintas sí conservan ambos ingresos, aunque una sea excedente.

## Caja: escoger una sola convención

**Recomendación: libro de flujos físicos brutos.** Registrar entrada de efectivo recibido y salida de vuelto entregado por separado. No sumar además el neto como otra entrada.

`Efectivo esperado = apertura + entradas físicas registradas − salidas físicas registradas`.

Ejemplo: venta15, digital10, billete10 y vuelto5. Caja registra +10 y −5; aumento neto5. Digital10 no entra en gaveta. Registrar «venta neta5» y además «vuelto−5» daría aumento0: es doble descuento.

La reposición aumenta la gaveta, pero no es venta ni ingreso del cliente. Si procede de otro fondo del negocio, es un traslado con fuente/responsable/referencia; no crear ingresos del negocio de la nada. No es necesario construir contabilidad general para identificar su procedencia.

El código inspeccionado de caja tiene CashRegister/CashShift/CashShiftClose; HU-CAJA-03 está futura. No afirmar que libro manual, reposición o anulación actual ya funcionan. El cierre actual basado en apertura + totales de ventas requiere cambio para mixtos.

## Reposición física: una solicitud no equivale a billetes

Flujo propuesto: SOLICITADA → APROBADA / RECHAZADA → ENTREGA_REGISTRADA → RECEPCION_CONFIRMADA; si hay diferencia, INCIDENCIA. Se pueden simplificar pantallas manteniendo separados aprobación y recepción.

La solicitud identifica caja, importe, motivo, solicitante y, si corresponde, devolución que la origina. ADMIN autoriza y define fuente/persona que llevará dinero. La entrega y recepción registran importe real y responsables; discrepancias no se silencian. Al confirmar recepción consistente se registra una sola entrada en caja. Reintento no repone dos veces.

Aprobar desde HTTPS no mueve billetes. Si nadie puede llevarlos o no existen fondos, la solicitud no está completada. Se admite aprobar un importe menor solo si el flujo lo explicita y la necesidad remanente queda visible.

**Dos permisos distintos:** autorizar reposición de fondos de caja y autorizar devolución al cliente. Pueden resolverse en una pantalla con dos decisiones explícitas; no hacer que aprobar reposición autorice cualquier salida del vendedor.

## Exceso digital y devolución en efectivo

La nueva idea del usuario es evaluar resolver excesos con efectivo y reponer caja si falta. Es una política comercial/contractual concreta que puede simplificar la ejecución, pero **no equivale al vuelto ordinario de un billete ni queda autorizada por prohibir nuevos yapeos**.

Con QR de importe fijo debería ser excepcional: segunda operación real, pago tardío u otro caso verificable. Un webhook repetido no genera exceso. La cuenta/origen y el beneficiario deben estar identificados; no pagar efectivo a quien solo presenta captura o conoce el importe. Con dos pagadores, mantener obligaciones por origen; una devolución total no necesita R2 porque se resuelve el aporte remanente de cada uno.

Recomiendo mostrar «Excedente por devolver» hasta autorización/entrega. El servidor calcula importe; el cajero no lo inventa. Registrar operación digital origen, autorización de cambio a efectivo, beneficiario verificado, salida de caja y resultado. No transformar el minimarket en servicio de retiro de saldo digital.

**Fuentes verificadas en esta pasada:** la [página oficial SDK QR](https://developers.izipay.pe/products/pay-with-qr/) describe QR por monto e interoperabilidad; no demuestra afiliación productiva de esta cuenta. Los [términos de QR de Interbank Negocios](https://interbank.pe/terminos-y-condiciones-para-el-uso-de-codigo-qr-link-de-pago-y-plataforma-de-pago-en-tiempo-real-de-izipay1) son de QR estático de esa app, excluyen reversas/extornos y restringen disposición en efectivo. No se extrapola automáticamente esa cláusula al SDK Web, pero exige consultar expresamente si y cómo permite resolver un sobrepago con efectivo. Tampoco extrapolar plazos de liquidación entre productos.

El proveedor debe aclarar también comisiones sobre exceso y riesgo de reversa posterior: entregar efectivo antes de liquidación puede exponer dinero propio del negocio. No descontar comisiones al cliente unilateralmente. No se ha hecho consulta comercial ni transferencia en esta revisión.

## Cancelación: depende de dinero recibido y mercadería, no solo de Sale

| Situación | Tratamiento |
|---|---|
| Nada recibido, sin entrega | Cancelar pedido e intento conservando referencia/seguimiento si hubo QR expuesto |
| Efectivo recibido, aún sin venta | Conservar entrada física; su devolución es salida registrada. No borrar el borrador y afirmar que no hubo dinero |
| Primer QR pagado y segundo pendiente | Conservar primer abono; cancelar/seguir segundo; devolver lo recibido por mecanismo aprobado |
| Digital y efectivo recibidos | Obligaciones por cada origen; efectivo se ejecuta con fondos y autorización; digital por ruta confirmada/permitida |
| Venta ya confirmada | Registrar cancelación/retorno y deuda sin borrar venta original. Stock se resuelve según entrega física y condición, no siempre vuelve a vendible |
| Pago llega después de cancelar | Se vincula al pedido cancelado y genera obligación; no acredita siguiente compra |

No sostener «antes de cerrar no hay nada irreversible»: transferencias y entrega de billetes pueden ocurrir antes de crear Sale. Pedir primero efectivo no elimina este hecho.

Para casos sin ajustes externos, el principio de conservación es: recibido = aplicado vigente + pendiente sin aplicar/devolver + reservado para devolución + efectivamente devuelto. Si se cancela una compra que recibió15, aplicado pasa a0 y deben resolverse15; si estaba vigente y total10, exceso5. Reposición no pertenece al recibido del cliente. Ajustes de redondeo del comercio se contabilizan aparte.

Si falta efectivo, registrar solicitud de reposición y obligación. Si ADMIN rechaza la reposición, la deuda no desaparece. Recomiendo no impedir indefinidamente el cierre por toda deuda digital: cuando se acepte esta política, cierre puede conservar deuda y responsable sin reescribir caja. Una entrega ya en curso o incierta exige conciliación/reserva y no puede darse por resuelta. Cierre con pendientes y devolución posterior requieren refinamiento explícito de RN-08/RN-10.

## Qué puede aplazarse y qué permanece necesario

Si el responsable confirma un incremento centrado en cobros y cancelación total, pueden aplazarse R2 para devoluciones parciales de productos, M2/triple límite, vales y puente Android. Eso no hace compatible por sí solo volver a depender de ADMIN para cada excepción; debe documentarse disponibilidad esperada y quién suministra el efectivo. Ventas normales siguen automáticas.

Se conservan reservas/idempotencia mínimas, historial por pago, autenticidad, conservación del dinero, caja, permisos y recuperación. Son necesarios para no duplicar cobros o salidas, incluso en una demo de tres escenarios.

Cambios sugeridos: HU-VEN-10 y HU-VEN-01c para aportes; HU-CAJA-03 para libro/reposición; HU-CAJA-02 para cierre; HU-VEN-06a/b/c para cancelación, beneficiario y destino físico; HU-VEN-02a/historial para constancias. Buscar IDs existentes antes de crear historias. No marcar futuros como implementados ni borrar políticas anteriores: registrar cambio de selección cuando se acepte.

## Casos mínimos del incremento

1. Todo QR15: confirmación externa válida produce una venta y stock una vez; captura/callback falso no acredita.
2. Mixto: digital10 + billete10 − vuelto5 = venta15; caja aumenta5.
3. Dos teléfonos7,50+7,50: dos operaciones inequívocas, una venta; eventos repetidos no duplican.
4. Cancelación tras primer pago7,50: pedido preservado y obligación7,50; no venta completa ficticia.
5. Dos operaciones digitales reales10 sobre compra15 con efectivo5: ingresos25, aplicado15, obligación10; repetición del mismo evento no genera obligación nueva.
6. Caja0, obligación10, reposición aprobada20: aprobación no cambia saldo; recepción20 añade20 una vez; devolución autorizada10 deja10. Reposición rechazada conserva deuda.
7. Respuesta perdida tras devolución/reposición y solicitudes concurrentes: recuperar misma ejecución; no repetir billetes ni efectos contables; probar PostgreSQL para concurrencia.
8. Pago tardío de pedido cancelado y proveedor/caja sin disponibilidad: conservar origen, estado y responsable; no marcar resuelto ni reasignar.

CP reales deben fijar permisos, precondiciones, mensajes, pasos y evidencia. Este documento no ejecutó estos casos. No abrió base operativa ni modificó código/08. Su fin es concretar una simplificación revisable y preservar el problema pendiente de elegibilidad y devolución del canal real.

## Aclaración posterior del responsable: integración del ciclo anterior

**16/11/2026 — información declarada por el usuario, no inspección del sistema anterior ni prueba de la cuenta.** El compañero gestionó una cuenta Izipay perteneciente a un integrante del grupo. Se realizaron pagos reales mediante un QR en el que, según recuerda el usuario, el cliente ingresaba el monto. El sistema de ventas no recibía confirmaciones automáticas ni sabía si se había pagado: el cliente mostraba la transferencia y el cajero finalizaba manualmente la compra.

**Corrección de procedencia:** ese antecedente no demuestra que se utilizara SDK Web QR, IPN, API, importe obligatorio o validación autenticada. La modalidad exacta sigue sin identificar. Tampoco acredita acceso actual propio/autorizado ni habilitación comercial del proyecto. Se retira cualquier expectativa de reutilizar una integración automática ya comprobada. El requisito nuevo sigue siendo automatizar la comprobación y asociar cada aporte a su pedido; el QR por sí solo no cumple esas dos funciones.

Los documentos llamados boletas/facturas en el ciclo anterior copiaban el formato para demostrar el flujo y **no tenían efecto tributario**, según el responsable. El profesor pide realismo con límites académicos. Esto no autoriza integración SUNAT ni demuestra emisión fiscal. Mantener el alcance de constancia interna RN-13/RN-26 y distinguir claramente cualquier representación académica de un comprobante fiscal, con la leyenda interna aplicable. Si se desea cambiar la pantalla o su denominación, proponerlo en HU/CA/CP antes de implementarlo.

Esta aclaración describe el antecedente; no cambia por sí sola la selección del nuevo canal, la política de devoluciones ni autoriza cambios en 08 o producto.
