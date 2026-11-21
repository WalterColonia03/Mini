# 7. Reglas de negocio · vista de la fuente principal

> **VISTA DERIVADA.** Fuente principal: [08 · planificación](08_Historias_de_Usuario.md). No editar requisitos aquí. Generada desde SHA256 `ad5e92486716bd32fe496dccdb54999cbbba530ddf03d799fc12c8415cc21aad`. Los cambios se hacen en08 y se regeneran estas vistas.

## 7.1 Resumen de reglas de negocio

| ID | Área temática | Descripción resumida | Historias de usuario relacionadas |
|---|---|---|---|
| RN-01 | Control de existencias | Una carga inicial única; recepción posterior directa con identidad propia; ajustes administrativos separados; SOL futuro | HU-INV-01a, HU-INV-01b, HU-INV-03; HU-SOL-05a/05b futuros |
| RN-02 | Pagos con billetera digital | El vendedor confirma el ingreso en Yape y el código de operación no puede repetirse | HU-VEN-07 |
| RN-03 | Control de vencimientos | En R1-PMV todo lote exige vencimiento posterior a la fecha de negocio de Lima; no se reciben ni venden lotes vencidos; ajuste físico vencido excepcional queda no vendible | HU-INV-01a, HU-VEN-01b, HU-VEN-01c, HU-PROD-06, HU-SOL-05a, HU-SOL-05b |
| RN-04 | Mermas y pérdidas | Toda baja de existencias exige declarar un motivo obligatorio | HU-INV-02 |
| RN-05 | Causas de baja | Causas exclusivas: vencimiento, daño o rotura, y robo o faltante | HU-INV-02 |
| RN-06 | Umbral de existencias mínimas | Cada producto conserva un umbral configurable, 10 por defecto; el alcance vigente incluye alertas según producto/categoría activos y vencidos físicos | HU-PROD-01, HU-PROD-02, HU-PROD-04, HU-SOL-01, HU-REP-05, HU-DASH-03 |
| RN-07 | Acceso a ventas | El vendedor consulta ventas propias según HU seleccionadas; ADMIN consulta historial global; costos excluidos de constancia | HU-VEN-05a, HU-VEN-05b |
| RN-08 | Anulación de ventas | Una venta solo se anula mientras el turno de caja permanezca abierto | HU-VEN-06a, HU-VEN-06b |
| RN-09 | Destino de mercadería | Al anular, el supervisor decide si el producto regresa a la venta o va a merma | HU-VEN-06c |
| RN-10 | Turno y efectivo de caja | Existe un único turno abierto global; apertura, movimientos confirmados y cierre determinan el efectivo esperado de forma irreversible | HU-CAJA-01, HU-CAJA-02, HU-CAJA-03, HU-VEN-01b, HU-VEN-01c, HU-VEN-06a |
| RN-11 | Movimientos de caja | Movimientos manuales de efectivo exigen monto mayor a cero, motivo y responsable | HU-CAJA-03 |
| RN-12 | Cuentas de empleados | El correo electrónico es identificador único e irrepetible | HU-USR-02, HU-USR-03 |
| RN-13 | Comprobantes futuros | Decisión futura fuera del horizonte académico | Fuera del horizonte académico |
| RN-14 | Costo de mercadería | Costo promedio ponderado calculado con precisión decimal de cuatro posiciones y visualizado con dos | HU-INV-01a/01b/02/03, HU-VEN-01c; HU-SOL-05a/05b y HU-REP-07 futuros |
| RN-15 | Moneda en caja | Los movimientos manuales de caja son exclusivamente en efectivo | HU-CAJA-03 |
| RN-16 | Reposición | Al aprobar la reposición, se puede cambiar el proveedor sugerido | HU-SOL-03 |
| RN-17 | Seguridad de acceso | 5 intentos fallidos consecutivos bloquean la cuenta durante 15 minutos | HU-AUTH-02, HU-AUTH-05 |
| RN-18 | Recuperación de clave | Código temporal de 4 dígitos para restablecer contraseña, válido 15 minutos | HU-AUTH-05 |
| RN-19 | Prioridad de salida | FEFO determinista por vencimiento, instante de ingreso e identificador interno del lote | HU-INV-01a, HU-VEN-01c, HU-SOL-05a, HU-SOL-05b |
| RN-20 | Detalle de pérdidas | Bajas por daño o robo exigen identificar el lote y describir lo ocurrido | HU-INV-02 |
| RN-21 | Identificación tributaria futura | Decisión futura fuera del horizonte académico | Fuera del horizonte académico |
| RN-22 | Seguridad en mostrador | Bloqueo preventivo de la pantalla de venta tras 5 minutos de inactividad | HU-VEN-01a |
| RN-23 | Inactividad de caja | Turno sin operaciones por 2 horas o más habilita el cierre administrativo | HU-CAJA-07, HU-DASH-03 |
| RN-24 | Seguridad de contraseñas | Clave de al menos 7 caracteres con mayúscula, minúscula y número | HU-USR-02, HU-AUTH-05 |
| RN-25 | Registro de venta | Venta, movimiento de efectivo, lotes, datos históricos y correlativo global se confirman juntos y sin duplicarse | HU-VEN-01c |
| RN-26 | Constancia interna | Constancia histórica consultable con correlativo global, sin costo de compra visible y con advertencia de no validez tributaria | HU-VEN-02a |
| RN-27 | Cálculo de IGV | Precios con IGV incluido; base redondeada a dos decimales e IGV residual para que ambos sumen exactamente el total | HU-PROD-02, HU-VEN-01b, HU-VEN-01c, HU-VEN-02a, HU-REP-07 |
| RN-28 | Costo histórico de venta | Conservar el costo que tenía el producto al venderse | HU-VEN-01c, HU-REP-07 |
| RN-29 | Autorización de R1-PMV | Cada cuenta tiene un único rol; separar consulta y operación conforme a matriz vigente | HU-AUTH-01, HU-AUTH-03, HU-PROD-02, HU-INV-01a, HU-CAJA-01, HU-VEN-01b, HU-VEN-01c, HU-VEN-02a, HU-CAJA-02 |
| RN-30 | Venta en preparación | Solo existe con al menos una línea; no altera caja ni stock, se descarta expresamente al salir y bloquea el cierre mientras permanezca activa | HU-AUTH-03, HU-VEN-01b, HU-VEN-01c, HU-CAJA-02 |

---

## 7.2 Reglas de negocio en detalle

---

<a id="RN-01"></a>

### RN-01 · Primera carga de existencias y entradas posteriores

**Área:** Control de existencias

La carga inicial directa se habilita una sola vez por producto y únicamente mientras ese producto no tenga una carga inicial confirmada. Puede contener uno o varios lotes y se considera realizada solo cuando la operación completa termina correctamente. Dos intentos simultáneos no pueden producir dos cargas: como máximo uno se confirma y cualquier segundo intento se rechaza sin modificar lotes, existencias ni costo.

Después de esa confirmación, ALMACENERO registra recepciones ordinarias directas con identidad propia, autor, lotes, cantidades, costos e idempotencia (DOC-03AB-01/03AI-01). La autorización de compra se gestiona fuera del sistema como política adoptada en este corte. HU-SOL-01..05b permanece futuro. ADMIN registra regularizaciones por conteo mediante HU-INV-03, identificadas como ajustes y nunca como nueva carga inicial o compra ficticia.

---

<a id="RN-02"></a>

### RN-02 · Confirmación externa del pago con Yape

**Área:** Pagos con billetera digital

Cuando el cliente paga con Yape, la responsabilidad de confirmar que el dinero realmente llegó corresponde únicamente al vendedor, quien debe revisar el pago directamente en el teléfono o medio habitual de Yape de la bodega antes de cerrar la venta. El sistema del minimarket no se comunica con Yape ni confirma por sí solo la llegada del dinero.

Una vez comprobado el abono, el vendedor copia el código o número de operación mostrado en ese pago y lo registra en el sistema. El sistema exige este código de manera obligatoria e impide volver a utilizar un código ya registrado en un cobro anterior, evitando que una misma constancia de pago se use en dos ventas distintas.

---

<a id="RN-03"></a>

### RN-03 · Bloqueo obligatorio de lotes vencidos

**Área:** Control de vencimientos

La fecha de negocio se obtiene de un reloj controlado por el sistema y se evalúa en la zona `America/Lima`. Ningún lote cuya fecha de caducidad sea igual o anterior a esa fecha puede registrarse por carga inicial/recepción ordinaria ni venderse. Como excepción de conteo físico, ADMIN puede registrar existencia vencida encontrada con fecha fiable, motivo y costo conforme a RN-14; queda inmediatamente no vendible y no simula una compra. Los lotes existentes en esa condición quedan bloqueados y no cuentan como existencias vendibles.

La línea base histórica R1-PMV abarcó exclusivamente productos enlatados sujetos a vencimiento. Para el catálogo actual, DOC03-01 (decisión del usuario del 09/11/2026) admite productos de cualquier categoría activa, vendidos por unidad (`UND`) y con vencimiento obligatorio: todo lote exige una fecha de caducidad. Productos sin vencimiento o vendidos por peso quedan fuera de esta ampliación y no aparecen como opción en sus pantallas.

---

<a id="RN-04"></a>

### RN-04 · Motivo obligatorio en toda baja de mercadería

**Área:** Mermas y pérdidas

Cada vez que ADMIN o ALMACENERO registre una baja de mercadería, debe indicar obligatoriamente la razón de esa salida antes de que el sistema descuente las unidades de las existencias. No se admiten bajas sin justificación.

---

<a id="RN-05"></a>

### RN-05 · Causas reconocidas para dar de baja mercadería

**Área:** Mermas y pérdidas

El sistema reconoce únicamente tres causas para retirar mercadería de los estantes y almacenes:

- **Vencimiento:** cuando la fecha de caducidad del lote es igual o anterior al día de hoy.
- **Daño o rotura:** cuando el producto sufre golpes, abolladuras o roturas físicas, pero todavía no estaba vencido.
- **Robo o faltante:** cuando se constata la pérdida de unidades; no depende de la fecha de caducidad, pero exige identificar de qué lote se perdió la mercadería y redactar una explicación de lo ocurrido.

No se admiten motivos genéricos ni causales distintas a estas tres.

---

<a id="RN-06"></a>

### RN-06 · Alerta visual de existencias mínimas

**Área:** Alerta de existencias mínimas

Cada producto conserva una cantidad mínima configurable, expresada como un entero entre 0 y 999999 inclusive. El valor predeterminado al registrarlo es de 10 unidades; si el administrador no indica otro valor, el sistema guarda 10. El máximo aplica a alta y edición en formulario, servicio y base de datos (PROP-03C-LIMITES ratificada por delegación expresa el 12/11/2026; no se atribuye aceptación al «continúa» anterior). La redacción histórica exigía entero no negativo sin tope superior.

El alcance vigente exige alerta de stock vendible igual o inferior al mínimo configurado para producto y categoría activos, de forma coherente en catálogo, stock y panel mínimo. Los vencidos físicos se muestran aunque estén comercialmente inactivos. SOL/REP/DASH completos siguen futuros; no se atribuye su entrega a esta alerta.

---

<a id="RN-07"></a>

### RN-07 · Visibilidad de ventas según el trabajo del empleado

**Área:** Acceso a ventas

En la pantalla de venta del mostrador, el vendedor puede consultar únicamente las ventas que él mismo ha cobrado durante su turno abierto. El historial consolidado de todos los turnos y vendedores queda reservado para una cuenta con rol `ADMIN` conforme a `HU-VEN-05b`, seleccionada para R1 de consolidación; “dueño” describe a la persona del negocio y no constituye un cuarto rol técnico en R1-PMV.

---

<a id="RN-08"></a>

### RN-08 · Anulación de ventas únicamente en turno abierto

**Área:** Anulación de ventas

Una venta solo puede anularse en el mostrador mientras el turno de caja en el que se cobró permanezca en estado abierto. Si el turno ya fue cerrado o se forzó su cierre, no se permite anular la venta en la pantalla del cajero para proteger el dinero contado del turno. Cualquier reclamo posterior se atiende de forma administrativa fuera del sistema.

---

<a id="RN-09"></a>

### RN-09 · Destino de la mercadería devuelta por anulación

**Área:** Destino de mercadería

Cuando se autoriza anular una venta con devolución física del producto, el supervisor debe indicar qué se hace con las unidades devueltas:

- Si el producto se encuentra en buen estado y sigue vigente, regresa a su lote original como existencia vendible; estar íntegro no vuelve vendible un lote vencido. El destino del vencido y la evidencia de devolución se refinan antes de seleccionar esta función futura.
- Si el producto está dañado o abierto, se traslada directamente a baja por merma y no regresa a la venta.

---

<a id="RN-10"></a>

### RN-10 · Apertura de turno en caja única

**Área:** Turno de caja

En todo el minimarket existe una sola caja y puede haber como máximo un turno abierto global. Al comenzar su labor, el vendedor declara en soles el efectivo inicial disponible para dar vuelto. El monto debe ser numérico, tener como máximo dos decimales y ser igual o mayor que cero. La apertura queda ligada a ese vendedor y conserva el instante del sistema; se almacena de manera inequívoca y se presenta con fecha y hora de Lima.

El efectivo esperado se obtiene de un registro de movimientos confirmados:

`Efectivo esperado = dinero inicial + ingresos confirmados de efectivo - salidas confirmadas de efectivo`.

En R1 de consolidación, los ingresos posteriores a la apertura son los totales de las ventas en efectivo confirmadas; el efectivo entregado por el cliente y el vuelto no se suman por separado. Cuando se implementen movimientos manuales o anulaciones, estos aportarán ingresos o salidas confirmados sin cambiar la fórmula.

Para cerrar, el vendedor responsable declara un monto contado numérico, no negativo y con máximo dos decimales. La diferencia es `dinero contado - efectivo esperado`: cero significa cuadre exacto, un valor positivo sobrante y uno negativo faltante. El cierre se confirma una sola vez y es irreversible. Un turno cerrado no admite ventas, reanudación ni un segundo cierre.

El cierre y el cobro concurrentes se resuelven como operaciones excluyentes: si la venta se confirma primero, queda incluida en el efectivo esperado; si el cierre se confirma primero, el cobro se rechaza. Nunca puede quedar una venta confirmada fuera del cierre del turno al que pertenece.

---

<a id="RN-11"></a>

### RN-11 · Registro obligatorio de movimientos manuales de dinero

**Área:** Movimientos de caja

Cada movimiento manual de efectivo en la caja —sea un ingreso o un retiro de dinero que no provenga directamente de una venta— exige un monto mayor que cero, el motivo de la operación, el responsable que lo autoriza, la fecha y la hora exacta.

---

<a id="RN-12"></a>

### RN-12 · Correo electrónico como identificador irrepetible

**Área:** Cuentas de empleados

Cada empleado se identifica en el sistema por su dirección de correo electrónico. No se permite crear ni activar dos cuentas con el mismo correo. Si se intenta registrar un correo ya existente, la operación es rechazada.

---

<a id="RN-13"></a>

### RN-13 · Comprobantes electrónicos tributarios futuros

**Área:** Comprobantes futuros

Esta regla constituye una decisión futura fuera del horizonte académico. Cuando en etapas posteriores se decida emitir comprobantes con valor fiscal, se adaptarán las series y envíos al canal autorizado correspondiente. Mientras tanto, el sistema solo genera constancias para control interno del negocio, sin denominarlas boleta o factura.

---

<a id="RN-14"></a>

### RN-14 · Promedio móvil sobre existencia física registrada

El costo de entrada es decimal positivo con hasta cuatro posiciones. El costo promedio se calcula con todas las unidades físicas registradas, incluidas vencidas pendientes de baja; disponibilidad comercial y valoración son conceptos diferentes. La carga inicial usa suma(cantidad×costo)/suma(cantidad). La recepción posterior usa `(Q×C + q×c)/(Q+q)`, con Q físico/C promedio bloqueados dentro de la transacción. Resultado HALF_UP4; presentación HALF_UP2.

Venta, baja y ajuste negativo retiran unidades al promedio vigente sin reponderar costos de los lotes restantes. La expiración sola no altera el promedio. Cuando stock físico total=0, promedio vigente=0; snapshots de salidas conservan el costo previo. Ajuste positivo con stock previo usa su promedio; sin stock exige costo positivo documentado y fuente/motivo, o se rechaza para investigar. No inventar costo histórico desconocido ni recalcular ventas pasadas con el costo de hoy.

DOC-03AH-01 y sus C-01..04 detallan ejemplos, concurrencia y tratamiento de legado. Política de control interno aceptada12/11. En14-E se implementaron entrada sobre físico, promedio conservado en salidas, puesta a cero al agotarse y captura de costo en baja/ajuste. La verificación es acotada; legado operativo, captura documentada con físico0 y concurrencia conservan sus pendientes en [ETAPA-14](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e). No acredita conformidad contable/fiscal.

---

<a id="RN-15"></a>

### RN-15 · Movimientos manuales exclusivamente en efectivo

**Área:** Moneda en caja

Los ingresos y retiros manuales que se registran directamente en el cajón de la caja corresponden únicamente a dinero en billetes y monedas. No se registran movimientos manuales con medios de pago digitales.

---

<a id="RN-16"></a>

### RN-16 · Elección de proveedor al aprobar reposiciones

**Área:** Reposición

Al revisar una solicitud de reposición de mercadería, el dueño o administrador puede confirmar el pedido con el proveedor sugerido por el empleado o cambiarlo por otro proveedor habitual si ofrece mejores precios o entrega más rápida.

---

<a id="RN-17"></a>

### RN-17 · Bloqueo de cuenta por intentos fallidos de acceso

**Área:** Seguridad de acceso

Cinco intentos fallidos consecutivos bloquean el identificador normalizado durante 15 minutos, con comportamiento uniforme para identificador reconocido, inexistente o cuenta inactiva, evitando revelar existencia/estado. El reset administrativo y desbloqueo explícito siguen DOC-02-04; un cambio de correo o reactivación no limpia silenciosamente la sanción. La recuperación de contraseña lleva su propio contador de códigos erróneos y suspende ese flujo durante 15 minutos sin revelar si el correo pertenece a una cuenta. Un ingreso o código válido reinicia únicamente el contador de su flujo. La pantalla informa los minutos restantes sin exponer datos sensibles.

---

<a id="RN-18"></a>

### RN-18 · Código temporal para recuperar contraseña

**Área:** Recuperación de clave

Cuando un empleado olvida su contraseña, solicita un código numérico temporal de 4 dígitos que se envía a su correo. Dicho código tiene una validez de 15 minutos y solo sirve para un único uso; al utilizarse o vencerse el plazo, queda sin valor.

---

<a id="RN-19"></a>

### RN-19 · Salida de productos vendiendo primero lo que vence antes

**Área:** Prioridad de salida

Al confirmar una venta, el sistema descuenta las existencias mediante un orden FEFO total y determinista:

1. fecha de vencimiento más próxima;
2. instante de ingreso al almacén más antiguo;
3. identificador interno inmutable del lote más bajo.

El instante de ingreso lo asigna el sistema al confirmar la entrada, se conserva en UTC y se presenta en la hora de Lima. El número comercial del lote no se usa para el último desempate porque puede contener letras. En R1-PMV todos los lotes controlan vencimiento; si en un release futuro se admiten productos sin vencimiento, su política de salida deberá aprobarse antes de incorporarlos.

---

<a id="RN-20"></a>

### RN-20 · Declaración obligatoria en pérdidas por daño o robo

**Área:** Detalle de pérdidas

Toda baja de mercadería motivada por rotura, daño físico o robo exige indicar obligatoriamente de qué lote proviene la mercadería afectada, cuántas unidades se perdieron y redactar una descripción del incidente ocurrido, guardando la identidad del empleado que reporta la pérdida.

---

<a id="RN-21"></a>

### RN-21 · Identificación de clientes en compras mayores

**Área:** Identificación tributaria futura

Esta regla constituye una decisión futura fuera del horizonte académico. La exigencia de datos formales del comprador según los montos de compra aplicará únicamente cuando el sistema se integre a un medio oficial de facturación electrónica. En el registro interno del mostrador no se exige esta validación.

---

<a id="RN-22"></a>

### RN-22 · Bloqueo preventivo de la pantalla por inactividad

**Área:** Seguridad en mostrador

Si la pantalla de ventas en el mostrador permanece sin uso durante 5 minutos continuos, se bloquea de manera automática para proteger el cajón del dinero. Para continuar atendiendo, el vendedor activo debe volver a escribir su contraseña.

---

<a id="RN-23"></a>

### RN-23 · Detección de turnos olvidados para cierre administrativo

**Área:** Inactividad de caja

Si un turno de caja permanece abierto durante 2 horas consecutivas sin registrar ninguna venta ni movimiento de dinero, se clasifica como turno inactivo u olvidado. En la funcionalidad futura HU-CAJA-07, esta situación habilita revisión administrativa y un cierre forzado trazable. Si no existe arqueo físico, contado y diferencia quedan «No declarado»: nunca se inventa un cuadre. El cierre original es irreversible; la aprobación futura HU-CAJA-06 agrega revisión y observación sin alterar importes ni reabrirlo.

---

<a id="RN-24"></a>

### RN-24 · Requisitos de seguridad para contraseñas

**Área:** Seguridad de contraseñas

Toda contraseña nueva que se cree o modifique debe tener como mínimo 7 caracteres, incluyendo al menos una letra mayúscula, una letra minúscula y un número. Esta condición se exige al crear cuentas o restablecer contraseña mediante ADMIN; también se aplicará al flujo de recuperación cuando sea seleccionado y refinado.

---

<a id="RN-25"></a>

### RN-25 · Registro completo e irrepetible de la venta

**Área:** Registro de venta

Al confirmar una venta en el mostrador se guardan juntos la cabecera, los detalles históricos, las asignaciones de lote, el movimiento de efectivo por el total vendido, el descuento de existencias y el correlativo. Si falla cualquier parte, no se confirma ninguna.

Cada intento lógico de cobro usa un mecanismo de idempotencia: un doble clic, reenvío o reintento devuelve el resultado de la misma venta y nunca crea otra, repite el movimiento de caja ni descuenta nuevamente el inventario. Ante cobros concurrentes se revalidan turno, producto y lotes dentro de la operación, de modo que las existencias jamás quedan negativas.

El correlativo interno tiene formato `V-00000001`, es global para el minimarket, ascendente, único e inmutable. No se reinicia por turno ni por fecha y un número ya confirmado nunca se reutiliza. El efectivo esperado aumenta por el total de la venta, no por el monto entregado antes de dar vuelto.

---

<a id="RN-26"></a>

### RN-26 · Constancia interna numerada sin validez tributaria

**Área:** Constancia interna

Cada venta confirmada conserva el correlativo asignado por RN-25. Su constancia se reconstruye exclusivamente con la fotografía histórica de esa venta: nombre del producto, cantidad, precio cobrado e importe por línea; fecha y hora de Lima, vendedor, caja, base, IGV, total, efectivo recibido y vuelto. El costo de compra o costo promedio se conserva internamente para reportes, pero nunca aparece en la constancia entregada al cliente.

Al terminar el cobro, el vendedor puede verla en pantalla, abrir una vista preparada para la impresión del navegador y volver a abrir la última constancia confirmada desde la pantalla de venta de su turno. Esta ruta mínima no sustituye los historiales seleccionados HU-VEN-05a y HU-VEN-05b, que tienen sus propios filtros/criterios y permisos.

La constancia debe exhibir con claridad la frase **«CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO»**. Puede incluir el nombre comercial y logotipo propio de la bodega, pero nunca logotipos, códigos o leyendas que simulen aprobación de SUNAT. La boleta o factura que corresponda se emite mediante el canal externo autorizado; su operación real debe confirmarse antes del piloto.

---

<a id="RN-27"></a>

### RN-27 · Cálculo de impuestos con total exacto

**Área:** Cálculo de IGV

Los precios de venta incluyen 18 % de IGV y se registran en soles con dos decimales. Cada importe de línea es `cantidad entera × precio unitario`, y el total es la suma exacta de esos importes.

Sobre el total de la venta se calcula:

`base = redondear_HALF_UP(total / 1.18, 2)`

`IGV = total - base`.

Base e IGV se expresan con dos decimales y, por construcción, siempre suman exactamente el total cobrado. No se calcula y redondea el impuesto de cada línea para luego sumarlo, porque eso podría producir diferencias de céntimos.

---

<a id="RN-28"></a>

### RN-28 · Conservar el costo que tenía el producto al venderse

**Área:** Costo histórico de venta

Cada venta registrada en el mostrador guarda el costo promedio que tenía cada producto exactamente en el instante en que fue vendido. Esto permite preparar un cálculo de margen comercial histórico sin sustituir el costo por promedios de compras posteriores. HU-REP-07 solo puede calcular un margen monetario cuando ingresos y costos tienen una base comparable documentada; si se desconoce el tratamiento del costo frente al IGV, informa «Margen no calculable con los datos disponibles». La política tributaria del costo requiere investigación antes de seleccionar ese reporte futuro. No demuestra rentabilidad neta del negocio: faltan gastos y otros factores. Cuando el costo histórico sea desconocido, el reporte debe informar esa cobertura y no presentar margen completo ni usar el costo actual como sustituto.

---

<a id="RN-29"></a>

### RN-29 · Autorización por rol exclusivo en R1-PMV

**Área:** Seguridad y permisos

Cada cuenta de R1-PMV tiene exactamente uno de estos roles: `ADMIN`, `ALMACENERO` o `VENDEDOR`. Para la demostración se preparan tres cuentas ficticias separadas, una por rol; no existe una cuenta multirrol ni un rol técnico adicional denominado “Dueño”.

| Operación del alcance vigente | ADMIN | ALMACENERO | VENDEDOR |
|---|:---:|:---:|:---:|
| Ingresar/salir propia sesión | Sí | Sí | Sí |
| Mantener personal/categorías/productos/proveedores | Sí | No | No |
| Consultar catálogo/proveedores/inventario | Sí | Sí | No; consulta POS vendible |
| Carga inicial/recepción | No | Sí | No |
| Baja de inventario | Sí | Sí | No |
| Ajuste físico | Sí | No | No |
| Consultar cargas/recepciones/bajas/movimientos | Sí | Sí | No |
| Abrir/preparar/cobrar/cerrar turno propio | No | No | Sí |
| Consultar ventas/constancias/turnos | Global | No | Solo propios; filtros según HU |
| Portal técnico | Sin permiso por rol comercial | No | No |

La constancia destinada al cliente nunca muestra costo de compra, incluso si la abre ADMIN. Las funciones futuras no aparecen como disponibles por figurar en esta matriz. DEC-12-PERMISOS-HISTORIAL-Y-MENU especifica solicitudes directas/propiedad/navegación.

Ocultar una opción no basta: toda operación se vuelve a autorizar del lado del servidor. Un rol sin permiso que use una URL o solicitud directa recibe una denegación y no consulta ni modifica datos.

---

<a id="RN-30"></a>

### RN-30 · Venta en preparación, salida de sesión y cierre de caja

**Área:** Mostrador y sesión

Existe una venta en preparación desde que la lista contiene al menos una línea de producto y hasta que se cobra o se descarta. La primera línea válida crea el único borrador `ACTIVE` del turno; quitar la última línea lo descarta dentro de la misma operación. Una pantalla de venta vacía no crea ni conserva un borrador `ACTIVE`. Prepararla no reserva ni descuenta existencias y no crea movimientos de efectivo.

El vendedor puede salir de su cuenta con el turno abierto. El sistema advierte que el turno seguirá abierto y ligado al mismo vendedor. Si además existe una venta en preparación, debe mostrar una confirmación explícita: confirmar la salida descarta todas sus líneas sin afectar caja ni existencias; cancelar la salida conserva la sesión y la venta. Después de volver a ingresar, el mismo vendedor recupera el turno abierto, pero no el borrador descartado. Otro vendedor no puede apropiarse de ese turno ni abrir uno paralelo.

Mientras una venta en preparación con líneas permanezca activa, el turno no puede cerrarse. El vendedor debe cobrarla, quitar su última línea o descartarla expresamente antes de confirmar el cierre.

---

## 7.3 Elementos fuera del alcance de este documento

Los aspectos meramente de apariencia visual o detalles de manejo interno del equipo no constituyen reglas de negocio. Esos puntos se definen únicamente cuando son indispensables en los criterios de aceptación de cada historia de usuario.

---

## 7.4 Marco tributario y límite del PMV

Durante el PMV, los precios del catálogo se interpretan como finales con el 18 % de IGV y su cálculo matemático se realiza conforme a la regla RN-27 para control y cuadre de la venta. DOC03-01 amplía las categorías admitidas sin modificar este cálculo uniforme ni incorporar clasificación tributaria por producto; su revisión normativa permanece en la etapa16.

La historia `HU-VEN-02a` emite exclusivamente una constancia de control interno de acuerdo con la regla RN-26. La emisión oficial que corresponda al régimen real debe resolverse por un canal autorizado externo; el repositorio no demuestra qué canal utiliza el negocio ni su aplicabilidad tributaria concreta.

---

## 7.5 Configuración operativa de caja única

El minimarket trabaja con una sola estación de cobro en el mostrador:

- Los turnos de caja son individuales y utilizados por un solo vendedor a la vez.
- No existen cobros simultáneos en dos cajas; todo el cobro físico se concentra en el puesto principal de la tienda.
- Mientras un turno permanezca abierto, nadie puede abrir un segundo turno de caja.
- Para comenzar a atender y vender mercadería, el vendedor debe abrir formalmente el turno registrando su dinero inicial en efectivo (RN-10).
- Salir de la cuenta no cierra el turno: se aplica RN-30 y el turno continúa ligado al vendedor responsable hasta su cierre formal.

---

## 7.6 Delimitación de alcance operativo y supuestos del sistema

Los puntos1–2 describen funcionalidades FUTURAS de anulación/devolución (no disponibles en R1). El punto3 es preparación de entorno de demostración, no evidencia de datos productivos:

1. **Atención de devoluciones solo en turnos abiertos (RN-08):**
   - El sistema permite anular ventas únicamente mientras el turno de caja donde se realizó la venta continúe abierto (`HU-VEN-06a`, `HU-VEN-06b`).
   - Las devoluciones de dinero de turnos pasados o trámites contables formales con notas de crédito tributarias se gestionan de forma manual y externa a la pantalla de venta.

2. **Revisión del producto devuelto (RN-09 / `HU-VEN-06c`):**
   - Al anular una venta en el mostrador, se evalúa si el producto devuelto está en condiciones de venderse: si está en buen estado y sigue vigente, regresa a su lote original como existencia vendible; si está abollado o dañado, se envía directamente a baja por merma (`HU-INV-02`).
   - El sistema no genera automáticamente pedidos a proveedores cuando un cliente devuelve un producto.

3. **Preparación previa de datos iniciales:**
   - Las tres cuentas ficticias de demostración —una `ADMIN`, una `ALMACENERO` y una `VENDEDOR`—, la categoría activa «Productos enlatados» y la caja única se preparan antes de comenzar a operar la tienda.
   - La preparación usa datos reproducibles y no introduce una cuenta multirrol ni contraseñas reales dentro de los documentos de planificación.
   - Los instantes técnicos se conservan en UTC; las fechas y horas que ve el usuario, así como la fecha de negocio utilizada para vencimientos, se presentan en `America/Lima`.

## 7.7 Aplicabilidad y complementos de este corte

RN02/08/09/11/15/16/18/23 describen funciones futuras; RN13/21 están fuera del horizonte fiscal actual. No se usan para exigir pantallas no seleccionadas. RN22 se selecciona antes del piloto; RN24 conserva requisito documentado, no certificación de seguridad integral.

Nuevos cobros no aceptan descuento discrecional (DEC-11-DESCUENTOS-ALCANCE); los históricos permanecen intactos. Límite venta/efectivo/apertura9,999,999.99; cierre acumulado hasta capacidad14,2 (DEC-11-TOPE-EFECTIVO-FORM). RN27 describe modelo interno de precios con 18% incluido; el régimen tributario/productos reales no se han confirmado y debe comprobarse aplicabilidad antes de uso real. La constancia RN26 no reemplaza canal oficial.

El detalle verificable aceptado de recepción/lotes, inventario, identidad, permisos, bloqueos, seguridad y consultas reside en el anexo de contratos de la fuente principal 08. ENCARGOS conserva procedencia histórica y remite a esa fuente. No se renumeran RN existentes. Toda exigencia nueva mantiene estado de implementación pendiente hasta evidencia propia.
