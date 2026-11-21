# Decisión PAY-CANAL-01 · Cobros sin comisión · 15/11/2026

**Fundamento de aceptación:** el usuario respondió «Necesito una alternativa sin comisión» a la propuesta de Yape Empresa/Ayudantes. Queda **ACEPTADA la restricción de cero comisión de cobro** y **DESCARTADA esa propuesta de pago para esta entrega**. Esto no selecciona automáticamente otro proveedor, no acepta verificación manual ni autoriza afiliaciones. Continúan: dueño ausente, protección ante empleados maliciosos, rapidez, transferencias pequeñas reales por personas autorizadas y prohibición de nuevos yapeos para devolver.

## Resultado de investigación oficial

| Modalidad | Hecho confirmado | Limitación / disposición |
|---|---|---|
| Yape común por QR | Yape publica gratuidad de yapear y de pagos por QR; distingue productos con comisión como Empresa y POS | Candidato para una prueba pequeña de recepción. No se verificó consulta delegada gratuita ni API de abonos; no entregar la sesión o claves al cajero |
| QR Plin de Interbank | Interbank declara recepción sin comisión, acepta transferencias desde Yape y requiere cuenta en soles afiliada a Plin | Candidato alternativo de recepción. No hay prueba en la cuenta del usuario ni consulta delegada/API gratuita verificada. Costos de la cuenta se comprueban aparte |
| QR Plin de BBVA | BBVA publica transferencias sin comisión y recepción desde Yape por número o QR | Misma limitación: no se verificó perfil de empleado de solo consulta ni confirmación para Django |
| Yape Empresa/Ayudantes | Consulta delegada con comisión publicada | DESCARTADO por la decisión del usuario; no volver a solicitar su aceptación como opción vigente |
| QR Izipay de App Interbank Negocios | Sus condiciones del09/03/2026 publican comisión QR de3,44% + IGV | No presentarlo como gratuito ni confundirlo con QR Plin personal. Las páginas antiguas de izipayYA no prueban condiciones actuales |

Fuentes consultadas el15/11/2026: [Yape: comisiones](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/yape-cobra-comisiones), [Yape: pagos QR](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/32--es-gratis-realizar-pagos-con-qr), [Plin Interbank para cobros](https://interbank.pe/es/canales-digitales/plin/plin-negocios), [Plin BBVA](https://www.bbva.pe/personas/servicios-digitales/plin.html), [condiciones QR Izipay dentro de App Negocios](https://interbank.pe/terminos-y-condiciones-para-el-uso-de-codigo-qr-link-de-pago-y-plataforma-de-pago-en-tiempo-real-de-izipay1).

La gratuidad del envío, del cobro, de la cuenta bancaria y de una eventual integración son cuatro afirmaciones distintas. Tampoco se infiere que un producto para persona natural sea una cuenta empresarial del minimarket. En la exposición la titularidad del receptor debe describirse con veracidad; no hay empresa constituida ni RUC empresarial del proyecto. El QR existente todavía no tiene titularidad/canal verificados.

## Lo que queda sin resolver

Se encontraron formas de **recibir sin comisión**, pero no se verificó una solución oficial que reúna simultáneamente recepción gratuita, consulta del empleado sin acceso a fondos y confirmación independiente para esta aplicación. Esto es un límite de la investigación, no una afirmación de que no exista ninguna solución en el mercado.

Un QR comunica el destino; no informa a Django de que llegó dinero. Conocer el importe, un código escrito o una captura del comprador no permite comprobar un abono inexistente. Yape recomienda revisar movimientos del receptor y ofrece Ayudantes para la consulta del equipo, opción que aquí se descartó por costo. [Recomendación oficial contra yapeos falsos](https://www.yape.com.pe/preguntas-frecuentes/enviar-y-recibir-yapeos/como-identifico-un-yapeo-falso).

No resolver esta brecha compartiendo contraseña/sesión bancaria, fijando un teléfono con la app bancaria abierta, leyendo notificaciones como supuesto comprobante bancario ni atribuyendo autenticidad a una referencia inventada por el cajero. Ninguna de esas medidas demuestra un canal bancario de solo lectura. Las notificaciones pueden ser auxiliares para una persona, pero no se aceptaron como fuente automática de pago del sistema.

## Recomendación acotada y alternativas pendientes

1. **Recepción para la demostración:** evaluar primero una cuenta Yape común ya disponible y autorizada para recibir una transferencia pequeña; si hay una cuenta Plin existente, su QR interoperable es otro candidato. No abrir cuentas ni cambiar el QR por esta recomendación. No añadir Plin como cuarto medio visible sin refinar HU/CA/CP; si se elige interoperabilidad, distinguir billetera del pagador y cuenta receptora.
2. **Comprobación sin dueño:** un responsable de turno distinto del cajero podría cotejar el movimiento desde un canal que el titular/banco le permita usar y registrar una comprobación humana. Es una alternativa operativa, NO ACEPTADA ni verificada: necesita disponibilidad de esa persona, acceso legítimo, separación de permisos y riesgo residual explícito. No requiere que sea el dueño, pero añade trabajo humano y no impide colusión. No cumple una exigencia de automatización plena.
3. **Si también se exige prescindir de ese cotejo humano:** falta un canal oficial independiente que pueda consultarse desde el sistema sin comisión. La investigación actual no lo acredita; no fabricar una integración para dar el requisito por cumplido. Las pruebas aisladas con proveedor simulado sirven al desarrollo y no sustituyen las transferencias reales elegidas por el usuario.

No se propone una segunda persona como decisión ya tomada ni se obliga al dueño a aprobar cada venta. Mientras el canal no esté resuelto se puede desarrollar y probar el resto del sistema, y diseñar el registro separado de intentos/abonos/aplicaciones, con estados honestos; el cobro real no se declara listo. Reintegros siguen dependiendo de una política delegada sin nuevos yapeos, conservando el dinero y el movimiento de caja cuando corresponda.

## Impacto y verificación

Se actualizan RN-02, CT-ENTREGA-ACADEMICA/C-02 y CP-ACA-002 en08, manteniendo IDs y recuentos. Se regeneran07/09/03 y el índice, y se sincronizan diseño02, tareas16, preparación14, objetivo y prompts. Los informes y JSON anteriores se conservan con su fecha/build; su propuesta de Ayudantes fue superada por esta respuesta. La validación de fuentes no es prueba bancaria ni funcional.

La revisión cruzada detectó además un resumen antiguo de RN-02 que aún hablaba solo de confirmación del vendedor y relacionaba únicamente HU-VEN-07. Se sincronizó con la fuente legítima, referencia inequívoca, cero comisión y relación con HU-VEN-07/10, conservando pendiente el mecanismo. El resumen no autoriza un checkbox como confirmación bancaria.

| Decisión/recomendación | Beneficio | Riesgo / costo / impacto |
|---|---|---|
| Cero comisión de cobro, aceptada | Respeta presupuesto universitario | Reduce opciones de delegación/integración. Otros gastos requieren investigación y aceptación independiente |
| QR común, candidato | Permite transferencias reales pequeñas sin comisión publicada de la modalidad | Aún falta titular/cuenta y comprobar delegación; no resuelve fraude interno. Costo técnico bajo de mostrar QR, mayor para confirmación fiable |
| Responsable delegado, propuesta | No exige dueño presente ni acceso bancario del cajero | Trabajo humano, espera y colusión; requiere permisos y CP antes de implementar; impacto02/11/14 |
| Canal oficial independiente, investigación | Evitaría confiar en declaración del cajero | Disponibilidad, costo y elegibilidad no demostrados; no presupuestar una API inexistente |

**Ejecución de este corte:** investigación web y actualización documental. Cero afiliaciones, transferencias, pruebas funcionales y cambios de producto. [Validación y huellas](evidencias/PAY-SIN-COMISION-20261115/validacion.json).

**Cursor funcional conservado:** `02-DEMO-TRAZABILIDAD-01`. **Decisión paralela:** `PAY-CANAL-01-SIN-COMISION`; Ayudantes descartado, mecanismo restante abierto. No reabrir la consulta de la comisión2,95% ni interpretar silencio como aceptación de otra modalidad.


## Revisión posterior de alternativa propuesta por el usuario

Se examinaron los textos atribuidos a Gemini y se documentó [PROP-PAY-OBS-01](REVISION-PROPUESTA-GEMINI-PAGOS.md): puente Android como observación de avisos, con autenticación del dispositivo, persistencia y separación entre aviso/abono/aplicación. Es una propuesta de experimento; no se acepta autoconfirmación por monto ni se afirma compatibilidad real. Se corrigió la tarifa alegada de Mercado Pago y se confirmó que su documentación Yape sí contempla reembolsos; sigue sin satisfacer cero comisión. Continúan el cursor 02 y las decisiones de canal/reintegro. Esta investigación no sobrescribe la validación histórica de la decisión de costo.
