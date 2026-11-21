# Revisión de los prompts de auditoría del minimarket

**20 de noviembre de 2026 · Lima · alcance documental.** Se actualizaron los 18 prompts (00 preparatorio y etapas 01–17) y las cinco guías que comparten. El [índice de prompts](../LEEME.md) enlaza el bloque copiable de cada etapa. La fuente funcional es [08](../../08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA). El brief del responsable del 17/11 actualiza las decisiones económicas y de recepción del [traspaso del 16/11](TRASPASO-DISENO-PAGOS-ASTRA-ARGON-CLAUDE-20261116.md), que se conserva como antecedente.

## Qué debe demostrar el sistema

El profesor podrá entrar por HTTPS público, recorrer el trabajo de los tres roles y seguir una venta desde los productos y lotes hasta sus pagos, constancia interna, historial y cierre de caja. La referencia de producto es Django, caja única y un turno abierto. La dirección aceptada es efectivo, digital y mixto con QR estático de una cuenta Yape propia, cero comisión de cobro y atención ordinaria sin aprobación del dueño. Cada pagador ingresa el importe. Las compras admiten varios aportantes.

La prueba de mostrador propuesta es una venta de S/15. El primer celular aporta S/5, el segundo S/6 y el cliente entrega un billete de S/5 con S/1 de vuelto. El historial debe conservar los dos aportes digitales y el efectivo neto de S/4. El stock sale una sola vez y la caja aumenta S/4. Una consulta posterior por la venta debe recuperar cada aporte y su resolución. Si el aviso de otra compra cancelada llega mientras se atiende esta, queda asociado a la original solo con evidencia suficiente y en revisión en los demás casos. Un cargo real sobrevive a un error de confirmación de Django.

## Contrastes que cambiaron las instrucciones

| Hallazgo | Resolución en la planificación | Dónde comprobarlo |
|---|---|---|
| La HU pedía que el vendedor ingresara el código y declarara recibido el pago | QR administrado por ADMIN. La acreditación requiere evidencia del receptor y vínculo con un pedido previo. Puente y desafío pendientes de ensayo | HU-VEN-07, RN-02 y CP-HU-VEN-07-001/002 en etapas 10, 11 y 15 |
| El QR del brief es reutilizable y el pagador puede introducir otro importe | Mantener saldo pendiente, insuficiente, excesos, pagos de terceros, avisos huérfanos y tardíos. Nunca asignar por importe o tres dígitos solos | HU-VEN-10, CP-ACA-003 y [matriz de 30 escenarios](../PAGOS_YAPE_Y_MIXTOS.md) |
| El cierre actual suma el total de ventas al fondo inicial. RN-25 también generalizaba esa regla | El total de la venta solo coincide con el incremento de gaveta en efectivo íntegro. En mixto cuenta el efectivo neto, en digital el efecto físico es cero | RN-10, RN-25, HU-CAJA-02, CP-HU-VEN-10-001 en 09, 11–14 |
| La anulación de efectivo podía leerse como instrucción de hacer salir dinero de la gaveta | Conservar la deuda hasta entrega autorizada. Solicitud de reposición, aprobación, recepción física y pago tienen efectos separados | HU-VEN-06a/b, CT-ENTREGA-ACADEMICA/C-04 y CP-ACA-004 |
| El borrador descartable y el cierre que bloquea un carrito activo chocan con atender al siguiente cliente tras un pago incierto | Separar el pedido durable que contiene evidencia del borrador de trabajo. Conservar el vínculo antes de dejar libre el puesto. El diseño aún requiere implementación | RN-30, HU-VEN-07/CA-08..09 y etapas 02, 09–11 y 14 |
| El brief atribuía al vendedor «ventas del día» y dejaba abierto el papel del almacenero | El vendedor consulta sus ventas del turno abierto. ADMIN tiene consulta global. La calificación física de una devolución encaja en la ficha futura HU-VEN-06c. La autorización monetaria se decide aparte | HU-VEN-05a/05b/06c y RN-09/29 en 02, 12 y 14 |
| Referencias antiguas daban prioridad a una pasarela o a un verificador humano en cada venta | El ensayo principal usa Yape propio y el dispositivo del titular. Plin sin desafío comprobado y el cotejo excepcional permanecen en revisión. No se propone nuevo rol ni turno de verificación | RN-02, 02 diseño, 16 tareas y guía del ensayo |

## Cómo se reparte el trabajo

- **00** fija inventario y versiones. **01** cubre ingreso, bloqueo y acceso por rol. **02** cubre sesión y personal. En el corte vigente, 01-K solo aporta evidencia local y 02-E permanece PARCIAL.
- **03–08** preparan la mercadería que se podrá vender. Comprueban maestros, proveedor, lotes, recepción, stock vendible, vencimiento y merma. La reposición de inventario y el ingreso físico de fondos se auditan en sus respectivos módulos.
- **09–12** prueban caja, recuperación del pedido, cobro por aporte, stock FEFO, constancia e historial. **13–14** concilian totales y permisos entre roles. **15** prueba seguridad, concurrencia, recuperación y publicación. **16** comprueba cuenta, condiciones de uso, costos y alcance de la constancia. **17** requiere evidencia del mismo build público y de las pruebas monetarias autorizadas.
- Cada etapa conserva su informe, fallos conocidos, versión, evidencia y cursor. El inventario del 15/11 permanece fechado. El [estado general](ESTADO_GENERAL.md) mantiene el siguiente cursor en `02-DEMO-TRAZABILIDAD-01`.

## Evidencia y reproducción

Se contrastaron, entre otros, [ventas y descarte del borrador](../../r1-pmv/sales/services.py), [cierre de caja](../../r1-pmv/cash/services.py), [modelos de venta](../../r1-pmv/sales/models.py) y [roles](../../r1-pmv/identity/models.py). La inspección del árbol local es estática. El HEAD de referencia es `7816d3328115cf5aa5bcdd0985fffd795b3ae084`; el árbol contiene cambios locales previos, por lo que el commit por sí solo no describe esos archivos.

Se conservaron los IDs funcionales y la selección previa de 35 HU. Se revisaron el texto de historias, reglas, casos de uso, criterios y casos escritos, y se regeneraron 07, 09, 03 e índice a partir de 08. Se contrastó su contenido con una segunda generación en memoria y se verificaron los bloques copiables, sus salidas, los enlaces añadidos y las filas históricas de estado. El [registro de validación](evidencias/PROMPTS-YAPE-20261120/validacion.json) contiene resultados, huellas y límites. Para reproducir la derivación, ejecutar desde la raíz sobre una copia:

```powershell
python -B -X utf8 auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py
```

Versión 08 antes: c0aa262b2dceba783ffa08e61bcca985857d777f5ef38be7749c4dd99d47e632. Versión 08 de este corte: 3a8edfbf701b5bf40fce0e209a0219f44dce14686feb06a965b806aa0aaba10b. [Copia de los documentos previos](evidencias/PROMPTS-YAPE-20261120/documentos-previos.zip).

**Próxima comprobación decisiva.** Ensayar en el Galaxy A52s 5G con Android 14 declarado la recepción y distinción de dos pagos seguidos, el reenvío tras desconexión y la asociación con un pedido aun cuando otro cliente pague el mismo importe. Contrastar con los movimientos del titular y las condiciones de la modalidad. Si el teléfono pierde un pago o dos pedidos siguen siendo indistinguibles, mantener la operación en revisión. Antes de la demostración real hace falta también resolver quién puede devolver, a quién, por qué medio, con qué fondos y cómo se acredita la entrega si la caja está vacía. En este corte se verificaron documentos y código por lectura; siguen sin ejecutar los nuevos CP funcionales, la prueba del teléfono y la demostración HTTPS con dinero real.
