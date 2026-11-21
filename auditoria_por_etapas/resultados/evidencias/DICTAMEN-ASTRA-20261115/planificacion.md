# Revisión independiente de planificación para DICTAMEN-PAGOS-ASTRA

Fecha de corte: 15/11/2026, America/Lima. Alcance: inspección documental de pagos y sus dependencias. No se modificaron 08, 02, 16, vistas, etapas ni producto. No se ejecutó Django, navegador, cuenta bancaria o transferencia. `VERIFICADO DOCUMENTALMENTE` identifica lectura de documentos locales, no validación bancaria. Todo cambio enumerado abajo es `PROPUESTO`; no se convierte en `ACEPTADO`, `IMPLEMENTADO` ni `PROBADO` por esta nota.

Se leyeron primero PROTOCOLO_COMUN, CONTINUIDAD_Y_SEGUNDA_PASADA, ESTADO_GENERAL, OBJETIVO_Y_CRITERIOS_DE_ENTREGA, PAGOS_YAPE_Y_MIXTOS, DECISION-PAGOS-SIN-COMISION y REVISION-PROPUESTA-GEMINI-PAGOS. Después se contrastaron las secciones aplicables de 08, 02, 16 y vistas 07/09/03. El protocolo requiere alcance y autoridad explícitos; prevalece la instrucción de usuario de no cambiar requisitos ni cierres. Se conserva Etapa 01 = ingreso/bloqueo/acceso según rol; Etapa 02 = sesión/personal; cursor funcional `02-DEMO-TRAZABILIDAD-01`. Esto no ejecuta ni cierra una etapa.

## Referencias y huellas comprobadas

| Archivo | SHA256 obtenido en esta revisión |
|---|---|
| 08_Historias_de_Usuario.md | c0aa262b2dceba783ffa08e61bcca985857d777f5ef38be7749c4dd99d47e632 |
| 02_Diseno_Tecnico_R1_PMV.md | a5aceab0750baf743bbb32a9c89eff980ff3decd8fbfd4a3ed682b98e294a2ac |
| 16_Task_Breakdown.md | 2e56d849c74c2cb473c3c23c0fa48bee1762996c7b2d5138ad476d5a412fe0a0 |
| 07_Reglas_de_Negocio.md | 04b4eae110b96125bb6c91462818883ca1655638c088094c1115cee92a14ea4c |
| 09_Product_Backlog.md | 1aec09a63a08155acfc480de91361a12eddd9146177918f35adc90d362108f02 |
| 03_Matriz_de_Trazabilidad_y_Pruebas.md | f12db6f5565eb6464eb81f37f7772eea2d10e196a421d60173c9fb16daa38b53 |

Las tres vistas declaran en línea 3 exactamente la huella actual de 08. Es consistencia de versión comprobada, no demostración de corrección completa del generador ni de cobertura funcional. No se regeneraron. 08 conserva el corte de unificación 12/11 y el objetivo actualizado 15/11; las 75 HU, 35 seleccionadas, 40 futuras y 121 CP son recuentos declarados por 08 y por la validación heredada, no una nueva prueba funcional. Los resultados históricos 652/652, 634/634, Chrome y PostgreSQL conservan exclusivamente sus builds y alcances originales.

El informe previo cita tres adjuntos Gemini, dos distintos. `evidencias/REVISION-GEMINI-20261115/entradas.json` localiza los originales en `.codex/attachments`; el agente principal verificará su contenido y huellas. No debe declararse inexistente el original por no estar en el árbol del proyecto.

## Contrato vigente útil

| Fuente precisa | Hecho documental | Consecuencia |
|---|---|---|
| 08:5, 4099–4105, 5405–5433 | Cero comisión, dueño ausente, QR/Yape/mixto, no nuevos yapeos; selección del canal y política de reintegro pendientes | Restricciones aceptadas; la solución particular continúa propuesta |
| 08:3171–3238, HU-VEN-07/CA-01..09 | Fuente legítima, receptor ADMIN, registro del origen, no doble uso, no código corto global, conservación del abono | HU seleccionada, mecanismo no implementado ni demostrado |
| 08:3246–3302, HU-VEN-10/CA-01..05 | N abonos, E+Y=T, vuelto R−E, exceso digital separado, desglose y política de reintegro | Modelo monetario ya solicitado, insuficiente definir solo `medio=MIXTO` |
| 08:2770–2820, HU-VEN-01c/CA-01..06 | Efectivo, snapshots, FEFO, atomicidad e idempotencia | Mantener invariantes; reescribir alcance monetario solo con cambio aceptado |
| 08:5409 | VEN06a/b/c siguen fichas históricas W, pero son dependencias obligatorias por refinar del objetivo académico | No excluir devoluciones del cierre por su etiqueta W ni declararlas implementadas |
| 08:5435–5510, CP-ACA-001..006 | Publicación, dinero, abuso, devolución, rapidez y trazabilidad | Son casos diseñados; no ejecución demostrada |
| 08:5302–5375, CT-COHERENCIA-UI/C-01..04 y CP-VISIBLE-001..004 | Toda acción, mensaje, cifra, estado y promesa visible necesita requisito y evidencia | Antes de implementar, catálogo literal aceptado referido por HU/CA/CP |
| 08:4424–4441, RN-29 | ADMIN, ALMACENERO, VENDEDOR exclusivos; reautorización servidor | ADMIN es identificador de código del rol denominado administrador; no cuarto rol |
| 08:4198, HU-CAJA-01/CA-03, CP-HU-CAJA-01-002 | Una caja, un turno abierto global | Analizar dos cajas como amenaza; actual debe rechazar segundo turno. Multicaja exigiría decisión de alcance |
| 08:4382–4386, HU-VEN-02a/CA-03 | Constancia histórica con leyenda de control interno | No introducir integración SUNAT para aparentar comprobante fiscal |

## Brechas e inconsistencias que no resuelve una revisión favorable del canal

1. **Referencia aún presupuesta.** HU-VEN-07/CA-03 y CA-04 exigen código de operación completo/único; CA-01 y CA-08 requieren fuente legítima e identificación inequívoca. No puede implementarse el campo como código de tres dígitos, UUID del puente o texto inventado. Refinar referencia externa opcional si existe, identificador interno explícito, vínculo y evidencia suficiente; no usar un identificador local como prueba externa. HU-VEN-07/CA-02 aún formula la barrera como declaración del vendedor y su descripción alude a teléfono de bodega: incompletas frente al objetivo de empleado malicioso. La interpretación restrictiva de CA-01 impide un simple checkbox, pero el texto debe armonizarse antes de construir.
2. **Anulación no prueba salida.** HU-VEN-06a/CA-02 (08:3042) resta el efectivo esperado al confirmar anulación; CP-HU-VEN-06a-001 (08:3061) condiciona el resultado a reembolso confirmado. CT-ENTREGA-ACADEMICA/C-04 requiere hechos separados. Separar anulación comercial, obligación de reintegro y salida ejecutada; el dinero esperado solo cambia con salida efectiva contabilizada.
3. **Turno cerrado.** RN-08 (08:4175) manda reclamo posterior fuera del sistema; CT-ACA/C-04 y CP-ACA-004 requieren conservación/resolución sin reescribir cierre. Registrar expediente posterior vinculado y salida en turno/medio posterior autorizado. No reabrir caja histórica.
4. **Pago parcial y logout.** RN-30 (08:4451–4455), HU-AUTH-03/CA-02..03 (08:285–289), DOC-02-04/C-04 (08:4783) descartan borrador al salir/quitar última línea y permiten solo uno ACTIVE. Pedido con dinero requiere persistencia independiente; no conservarlo oculto en sesión ni borrarlo como carrito. Propuesta: separar edición activa de pedido cobrado parcialmente/en revisión, permitir aparcar el segundo sin borrar deuda y atender otro. Esto cambia planificación de 02/10 y no habilita multicaja por sí mismo.
5. **Contabilidad heredada de efectivo.** RN-25 (08:4368/4372), HU-CAJA-02/CA-02 (08:2363) y diseño 02:107 suponen `Sale.total` como único ingreso de gaveta. Al aceptar mixtos debe pasar a ingreso neto de efectivo aplicado, con digital y reintegros aparte. No sumar total de venta más aplicaciones. Ajustar constancia, historial, acta e indicadores (VEN02a, VEN05a/b, CAJA02/05; panel mínimo existente) sin incorporar todos los reportes W.
6. **Precio y stock después del dinero.** HU-VEN-01b/CA-05 (08:2725) explícitamente no reserva stock. No proponer reserva como existente. Si se propone reserva al iniciar cobro requiere CA/CP de expiración, concurrencia y liberación; alternativa de menor cambio: congelar precio aceptado del pedido, revalidar stock al confirmar, conservar abono y tramitar resolución si falta mercadería. Cambiar precio exige nueva aceptación, no recalcular deuda silenciosamente.
7. **Permisos delegados ausentes.** RN-29 no concede comprobar abonos/aprobar/ejecutar reintegros a empleados no ADMIN. La palabra «supervisor» de RN-09 (08:4185) no crea un rol. Proponer facultades individuales, acotadas, revocables y auditadas sobre cuentas de los tres roles; no dar ADMIN total ni compartir clave. DOC-02-04/C-01 (08:4771) impide cambios de rol/desactivación con turno abierto; `REVOCACION-TURNO` ya está propuesto en 16:11. Es dependencia relevante ante cajero sospechoso, no cierre de Etapa02 por este informe.
8. **Noticias heredadas no son estado actual.** 02:258 y secciones históricas siguen diciendo Yape futuro; el encabezado y 08 seleccionan ampliación. Son antecedentes explícitos, no razón para omitirla. 02:12/08:4101 rechazan «notificaciones como supuesto equivalente bancario», lo que no prohíbe evaluar una observación legítima con límites; el usuario exige precisamente reconsiderarla. Si se adopta una comprobación operativa basada en notificación, describir su confianza y aceptación residual, no llamarla API bancaria.
9. **Falsa certeza por cotejo.** Revisión Gemini propone pedir código antes de mostrar candidatos, útil para reducir apropiación oportunista. No prueba pertenencia frente a cajero coludido que conoce el pago ajeno, homónimos o código repetido. Un candidato único dentro de la lista local no demuestra que sea el del comprador. La aceptación debe especificar método de reclamación desde el pagador, límites, excepciones y conciliación; si faltan, permanece revisión.

## Propuesta de refinamiento HU/CA/CP, sin incorporarla

Los IDs `PROP-*` son provisionales y no se convierten en HUs numeradas aceptadas. Reutilizar los IDs actuales en vez de duplicar necesidad. Los nuevos nombres siguientes definen trabajos de refinamiento, con CA/CP sugeridos para el dictamen principal.

| Objetivo propuesto | HU/CA que se modifica o nuevo provisional | CP existentes y adiciones propuestas | Condición verificable |
|---|---|---|---|
| Entrada de aviso sin pagar | VEN07/CA01..04,08; PROP-CA-PAY-OBS-01 | CP-HU-VEN-07-001/002 + PROP-CP-OBS-01 | Dado aviso autenticado del dispositivo, registrar observación y origen; no crear dinero por texto del cajero ni aplicar por importe |
| Comprobar y vincular | VEN07/CA01,05,08; PROP-CA-PAY-LINK-01 | CP-ACA-003 + PROP-CP-LINK-01..04 | Dos pagos iguales/códigos repetidos/tercero/abono tardío no se asocian al pedido nuevo; ambigüedad conserva estado revisable |
| Deduplicación real | VEN10/CA03; RN02 | PROP-CP-PAY-DUP-01..03 | Repetición de evento, revisión de notificación y repetición de un mismo abono son dominios distintos; ninguna carrera aplica más saldo disponible |
| Pedido durable y pendiente | VEN01b/CA01,05, AUTH03/CA02..03, RN30; PROP-HU-VEN-PEND-01 | CP-HU-VEN-01b-001, CP-HU-AUTH-03-002 + PROP-CP-PEND-01 | Salir/aparcar/cancelar nunca borra dinero ni autoriza entrega; otro pedido puede atenderse solo según cambio aceptado |
| Mixto y varios abonos | VEN10/CA01..05, VEN01c/CA01..06, RN25 | CP-HU-VEN-10-001, CP-ACA-002 + PROP-CP-MONEY-01..05 | 3+7=10; efectivo 20 para porción10 da vuelto10; exceso digital pendiente; fallo confirmación conserva abono |
| Cancelación y reintegro parcial | VEN06a/b/c; RN08/09; PROP-HU-VEN-REINTEGRO-01 | CP-HU-VEN-06a/b/c-001, CP-ACA-004 + PROP-CP-REF-01..06 | Solicitar/aprobar/ejecutar distintos; límite acumulado y reserva ante ejecución incierta; dos reintegros concurrentes no exceden deuda |
| Delegación granular | RN29, USR03/04, DOC02-04; PROP-HU-USR-PERM-01 | CP-ACA-003/004 + PROP-CP-PERM-01..04 | Solo concesión individual vigente autoriza; autoaprobación, sesión antigua y petición directa rechazadas; cambio invalida autorizaciones pendientes |
| Conciliación y fondos pendientes | CAJA02/05, VEN05a/b, VEN02a; PROP-HU-CAJA-CONCILIACION-01 | CP-ACA-002/004 + PROP-CP-REC-01..03 | Movimientos receptores contra abonos/aplicaciones/salidas; cierre físico separado de digital; faltantes no se borran por cerrar turno |
| Receptor y disponibilidad | VEN07/CA07, CT-ACA/C03 | CP-HU-VEN-07-002 + PROP-CP-DEVICE-01..05 | QR versionado autorizado; pausa por receptor/dispositivo incierto; avisos tardíos del receptor anterior conservados y no aplicados al actual |
| UI exacta | CT-COHERENCIA-UI/C01..04 | CP-VISIBLE-001..004 y todos los CP de pago | Pantalla/botón/literal/variable/estado/rol/ruta/error se registra antes de UI; evidencia pública del mismo build |
| Publicación y latencia | CT-ACA/C01,05 | CP-ACA-001/005 | URL HTTPS del proveedor admisible, sin localhost; DB durable y reinicio; tiempos banco/aviso/transporte/servidor/persona medidos aparte |

Recomendación de catálogo provisional para refinamiento, todavía no aceptado: «Pendiente de comprobar»; «Abono observado; falta vincularlo a esta compra»; «Pago en revisión. No solicite otro pago hasta consultar su estado»; «Abono sin aplicar: S/ {importe}»; «Reintegro pendiente»; «Reintegro ejecutado por {medio}»; «Consultar estado», «Dejar pendiente y continuar», «Solicitar cancelación», «Solicitar reintegro». Cada texto debe definir disparador, variables, permisos, evidencia exigida y CP; el catálogo no concede por sí solo una facultad ni afirma la existencia de la pantalla.

## Arquitectura y tareas para decisión

02 ya propone intento/abono/aplicación/reintegro; completar pedido durable y evidencia observada separada, origen de confianza, receptor versionado, dominio de referencias reales, bloqueos/constraints y orden de locks, historial apendicular con compensaciones, reserva de saldo a reintegrar, conciliación y migración de efectivo histórico. El adaptador Android debe ser reemplazable: el libro monetario no debe depender del texto de una notificación.

16 ya contiene `PROP-PAY-OBS-01`, `PAY-CANAL`, `PAY-REINTEGRO`, `PAY-MODELO`, `PAY-UI`, `PAY-INTEGRACION`, `PAY-ABUSO`, `DEMO-RAPIDEZ`, `DEMO-PUBLICAR`, `DEMO-CIERRE` y `REVOCACION-TURNO`. Reutilizarlas y subdividir provisionalmente:

1. PAY-MODELO-A: especificación/estado e invariantes independientes de canal, casos aislados de dinero exacto y persistencia de deuda. DoD propuesto: entradas/roles/errores/CA/CP/literales definidos, ninguna transferencia real, legado preservado.
2. PROP-PAY-OBS-01-A: ensayo de compatibilidad y condiciones del proveedor con receptor real; no construir integración completa antes del resultado. Debe decidir si hay evidencia suficiente y procedimiento sostenible.
3. PAY-CANAL-A: aceptar explícitamente nivel de confianza, custodia, vinculación, degradación y límites observados. Hasta entonces no habilitar cobro real.
4. PAY-REINTEGRO-A: aceptar medio y facultades individuales, reglas y límites; no inventar topes/plazos aceptados ni convertir excedente digital a efectivo automático.
5. PAY-MODELO-B/PAY-INTEGRACION: al autorizar implementación, adaptar venta/caja/stock/historial y probar migración, idempotencia, concurrencia PostgreSQL, caída y recuperación.
6. PAY-UI/PAY-ABUSO/DEMO-RAPIDEZ/DEMO-PUBLICAR: recorrido exacto por roles, URL pública del mismo build, tiempos descompuestos y ensayo humano de importes autorizados después de cumplir puertas anteriores.

No fijar Sprint, Fibonacci definitivo, horas o disponibilidad de personas por esta revisión. Refinar antes del compromiso. No marcar entregado porque el adaptador funciona ni porque el libro interno pasa pruebas ficticias: evidencia externa y asociación son puertas separadas.
