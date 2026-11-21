# Planificación principal del minimarket

<!-- FUENTE-PRINCIPAL-20261112 -->

**Revisión:14/11/2026.** Primera pasada:13 finalizada para panel mínimo;14 COMPLETADA para integración entre roles, navegador y persistencia delimitada.634/634 servidor,157 checkpointsChrome y19/19 PostgreSQL aislado. En segunda pasada acotada (`02-E`, sesión y personal): `H02E-01..04` implementados y verificados con `652/652` pruebas de servidor, Chrome real (`1366×768` y `390×844`) y `5/5` PostgreSQL `18.4`; `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01` continúan `FUTURO / NO DISPONIBLE` y `DOC-01-06/C-02` permanece `PARCIAL` ([Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e)). No cierra todos los módulos ni15–17. [Informe, versiones y cursor15-SEGURIDAD-BASELINE-01](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14). Después17, preparar00 y segunda pasada01–17.

**Corte: 12/11/2026. Autoridad funcional: este archivo08.** La planificación define el comportamiento esperado; código, interfaz y auditorías aportan evidencia de lo que ocurre. Una implementación existente no aprueba un requisito. Los documentos07/09/03 son vistas derivadas;01/02/14/16/20/21 describen contexto, diseño, ejecución y diferencias y deben ajustarse a esta fuente. No resuelven contradicciones alterando silenciosamente este contrato.

La decisión **DEC-FUENTE-UNICA-20261112** está ACEPTADA por instrucción expresa: unificar épicas, historias, prioridad MoSCoW, tamaño Fibonacci, descripción, criterios, casos escritos, datos y resultados esperados; auditar también cada promesa visible. Alcance:74 HU,33 seleccionadas para R1 y 41 futuras;8 ideas excluidas. La aceptación documental no autoriza implementación del producto ni cambia estados históricos de auditoría.

## Cómo leer y mantener esta fuente

- Una ficha define cada HU y conserva sus identificadores. Los 219 CA base se completan con 60 criterios de contratos y 4 criterios J de categorías. CT-COHERENCIA-UI añade 4 criterios transversales de veracidad visible. En esta revisión hay 113 casos escritos. La evidencia de ejecución se registra por caso y build.
- **PROPUESTA → ACEPTADA → IMPLEMENTADA → VERIFICADA.** Las 33 HU seleccionadas tienen especificación aceptada por delegación; los cambios requieren implementación autorizada y evidencia propia. Las 41 futuras mantienen criterios para refinamiento, no un compromiso de entrega ni aprobación de seguridad de todos sus detalles históricos.
- MoSCoW se aplica al horizonte R1: **M** obligatorio para el incremento coherente; **S** conveniente; **C** opcional por valor relativo; **W** fuera de este horizonte. Una función seleccionada/visible debe cumplir todos sus criterios aunque seaS/C; diferirla exige cambio explícito de alcance y retirar promesas engañosas.
- Puntos Fibonacci1/2/3/5/8/13 expresan tamaño relativo orientativo de la HU completa. Son propuesta de dimensionamiento del asesor; el equipo que implemente debe refinarlos. No equivalen a horas, trabajo restante, velocidad o compromiso de Sprint. Se conservan SP anteriores como procedencia. Las futuras mantienen tamaño histórico provisional.
- El inventario actual es ampliable: una necesidad descubierta se analiza y se registra con su fundamento de aceptación, impacto y pruebas;74 HU no son un máximo. Arquitectura/requisitos técnicos se trazan a02 y a la necesidad correspondiente, sin crear una HU por componente interno.
- Antes de cambiar una ficha: registrar motivo, fuente y decisión; actualizar RN/contratos relacionados, casos, vistas derivadas, tareas y evidencia afectada. Una contradicción es un hallazgo hasta resolverla con trazabilidad; no se reduce el requisito para acomodar un defecto.
- Un caso escrito indica cómo verificar; no demuestra que se ejecutó. La evidencia previa 434/434 en SQLite y la muestraPG18.4 se conservan con sus límites en [VERIFICACION](auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md). No verifican por sí solas los nuevos contratos ni toda la interfaz.

## Índice de épicas y dimensionamiento

| Épica | Objetivo | HU | R1 | Futuras | SP orientativos catálogo | SP R1 |
|---|---|---:|---:|---:|---:|---:|
| [EPIC-SEG](#EPIC-SEG) | Ingreso y personal | 13 | 8 | 5 | 49 | 30 |
| [EPIC-CAT](#EPIC-CAT) | Productos y proveedores | 14 | 11 | 3 | 36 | 31 |
| [EPIC-INV](#EPIC-INV) | Mercadería y reposición | 13 | 5 | 8 | 56 | 34 |
| [EPIC-VEN](#EPIC-VEN) | Ventas y caja | 18 | 9 | 9 | 76 | 51 |
| [EPIC-REP](#EPIC-REP) | Control del negocio | 16 | 0 | 16 | 51 | 0 |

Total:74 HU/268 SP orientativos; R1:146 SP. Referencia anterior:231 SP. Ninguno de estos totales representa un Sprint comprometido.

## Datos comunes y método de prueba

**F-BASE.** Base nueva y aislada por caso; fecha controlada 12/11/2026 en America/Lima. Roles ficticios: ADMIN, ALMACENERO, vendedorA, vendedorB y cuenta inactiva. Correos del dominio reservado `pruebas.invalid`; contraseñas ficticias de RN-24, sin reutilizar secretos reales. Cada variante restaura el estado descrito; no se encadenan pruebas sin indicarlo.

Lácteos activa; Leche1L activa, código INT-LECHE-1, UND, precio S/10.00, mínimo 10, vencimiento obligatorio. LoteA:10 unidades a2.0000, vence13/11/2026; loteB:10 a4.0000, vence12/12/2026; físico/vendible 20, promedio 3.0000. Arroz:5 unidades a2.0000, precio 5.00, mínimo 10, lote vigente. Los casos que requieren producto sin carga eliminan esa preparación únicamente en su clon. CAJA-01 comienza sin turno salvo que el caso requiera A abierto con S/100.00.

**F-COSTO** sustituye el estado de Leche: físico 18, promedio 3, ocho unidades vencidas pendientes de baja y diez vigentes; proviene de una carga20 y venta2 anterior al vencimiento. No agrega vencidos invisiblemente a F-BASE. Los lotesE y datos de informes son variantes explícitas, no cambios a la fórmula base. Los días futuros usados en pruebas son datos sintéticos con reloj controlado.

Para cada rechazo comparar antes/después: actor/sesión, borrador, producto, lotes, promedio, recepciones, ventas/detalles/asignaciones, correlativos, movimientos y turno, según alcance. UnHTTP400/403 no basta. En concurrencia registrar conexiones independientes, barrera que pruebe solapamiento, resultado serial permitido y ausencia de mutaciones parciales; SQLite no demuestra locks de PostgreSQL. En interfaz usar navegador real y evidencia sanitizada por rol/estado; Django Client no acredita una prueba visual.

Los númerosRUC son ficticios para probar formato, no identidad de empresa ni validación SUNAT. El fixture de margen con costo comparable es un supuesto de prueba explícito; no resuelve la política tributaria real.

## Fichas de historias

<a id="EPIC-SEG"></a>

## EPIC-SEG · Ingreso y personal

<a id="HU-AUTH-01"></a>

### HU-AUTH-01 · Ingresar con mi cuenta de trabajo

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como empleado de la bodega, quiero ingresar con mi correo y contraseña de trabajo, para acceder a las opciones de mi puesto y proteger la información del negocio.

**Reglas relacionadas:** RN-29. **Dependencias funcionales:** Ninguna.

**Orden de producto:** 1.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-01; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-12-PERMISOS-HISTORIAL-Y-MENU](#contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU), [DOC-01-06](#contrato-DOC-01-06).

#### Criterios de aceptación

<a id="HU-AUTH-01-CA-01"></a>

**HU-AUTH-01/CA-01.** Dado que tengo una cuenta activa con uno de los roles exclusivos `ADMIN`, `ALMACENERO` o `VENDEDOR`, cuando ingreso mi correo y contraseña correctos, entonces el sistema crea mi sesión y me conduce a las opciones autorizadas para ese único rol (RN-29).

**Precisión técnica01-E,14/11/2026.** El ingreso aplica el máximo254 del identificador de cuenta de DOC-02-04 después de recortar espacios exteriores, tanto en el campo como en el servidor. Un correo de254 puede autenticar;255 o más produce error de campo sin crear/incrementar intento. Se conserva `strip().casefold()` y no se canonicaliza IDNA sin diagnóstico de colisiones. Se acepta como corrección acotada del contrato ya aprobado y bajo el encargo de etapa01 de esta sesión; no crea política comercial ni amplía permisos. [Fundamento y revalidación](auditoria_por_etapas/resultados/soporte/01-E-disposiciones.md).

<a id="HU-AUTH-01-CA-02"></a>

**HU-AUTH-01/CA-02.** Dado que ingreso una contraseña incorrecta o un correo no registrado, cuando el sistema lo valida, entonces muestra el mensaje general «Correo o contraseña incorrectos» sin indicar cuál de los dos datos falló.

<a id="HU-AUTH-01-CA-03"></a>

**HU-AUTH-01/CA-03.** Dado que mi cuenta de empleado está inactiva, cuando ingreso credenciales correctas, entonces el sistema rechaza el acceso con el mismo mensaje general «Correo o contraseña incorrectos» sin dar información sobre el estado de la cuenta.

<a id="HU-AUTH-01-CA-04"></a>

**HU-AUTH-01/CA-04.** Dado que inicié sesión, cuando intento abrir por URL o solicitud directa una operación que RN-29 no permite a mi rol, entonces el sistema deniega el acceso, no expone los datos de esa operación y no modifica información.

#### Casos de prueba escritos

<a id="CP-HU-AUTH-01-001"></a>
##### CP-HU-AUTH-01-001 · Ingreso correcto de los tres roles

**Cubre:** HU-AUTH-01/CA-01. **Estado:** VERIFICADO EN MUESTRA01-E,14/11/2026; ingreso/sesión, sin aprobar los módulos de destino.
**Evidencia de ejecución:** [01-E, matriz y límites](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-e). Tres roles ficticios equivalentes en Client/ORM y Brave; credenciales aleatorias; sesiones aisladas o salida confirmada entre roles.120tests de regresión incluyen estos casos, no son120casos de estaHU.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN admin@pruebas.invalid; ALMACENERO almacen@pruebas.invalid; VENDEDOR vendedor.a@pruebas.invalid; clave ficticia PruebaSegura9!.

1. Abrir ingreso en tres contextos separados.
2. Escribir cada correo y su clave; confirmar.
3. Consultar opciones del rol y sesión persistida.

**Resultados esperados:** Los tres ingresan a sus opciones autorizadas con un único rol por cuenta y sesión nueva; no se convierten en cuentas multirrol.

<a id="CP-HU-AUTH-01-002"></a>
##### CP-HU-AUTH-01-002 · Credenciales rechazadas sin enumerar cuentas

**Cubre:** HU-AUTH-01/CA-02, HU-AUTH-01/CA-03. **Estado:** VERIFICADO EN MUESTRA 01-F (14/11/2026) sobre build `2cef34b5...`; sin análisis estadístico de tiempos.
**Evidencia de ejecución:** [01-F, matriz y límites](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-f) y [01-E](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-e). Suite `identity + audit01e_probes` (`128/128` OK; `83/83` núcleo Stage 01), [http-probes](auditoria_por_etapas/resultados/evidencias/01-F-20261114/http-probes.json) (`HTTP-01..07`: `no-store`, CSRF `403` con `attempts_delta: 0`, `PUT`/`DELETE` `405`, fronteras `254/255/319/320/321` y `\x00` con `0` filas en `LoginAttempt`, IDN Unicode vs punycode en `2` filas HMAC separadas, ingreso `254` normalizado con `\u00a0`/mayúsculas/tab y `next=//evil.invalid` bloqueado) y [chrome-manifest](auditoria_por_etapas/resultados/evidencias/01-F-20261114/chrome-manifest.json) (`C01..C09` + `C20` en `1366×900` y `390×844`). Canonicalización IDNA y tráfico NAT global siguen abiertos.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Variantes: correo ficticio registrado + clave Erronea1!, nadie@pruebas.invalid+PruebaSegura9!, inactivo@pruebas.invalid+PruebaSegura9!, ambos campos vacíos.

1. Restaurar intentos antes de cada variante.
2. Enviar ingreso y revisar mensaje, campo de clave y cookies.
3. Intentar abrir una ruta protegida.

**Resultados esperados:** Las tres credenciales inválidas reciben el mismo mensaje Correo o contraseña incorrectos; no se revela qué dato falló ni el estado de cuenta. Vacíos muestran validación de campo. No hay sesión autenticada ni cambios de stock/caja.

**Fronteras complementarias01-E:** cuenta ficticia con correo254 y clave válida ingresa incluso con mayúsculas/espacios exteriores; POST alterado con correo255/319/320/321 se rechaza por longitud y no crea intentos. Evidencia del sublote01-E separada de los casos históricos; no aprueba tráfico, IDNA, admin técnico ni toda laHU.

<a id="CP-HU-AUTH-01-003"></a>
##### CP-HU-AUTH-01-003 · Permisos por URL y petición directa

**Cubre:** HU-AUTH-01/CA-04. **Estado:** EJECUTADO PARCIAL en01-E,14/11/2026; identity y muestras de rutas ajenas, no RN-29 global.
**Evidencia de ejecución:** [01-E, matriz y límites](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-e). Pruebas de permisosidentity y Client/ORM; Brave visitante/almacenero/vendedor ante empleados, destino next denegado. Negocio vacío: no demuestra conservación de datos comerciales preexistentes.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** VENDEDOR intenta alta de producto; ALMACENERO intenta cobro; ADMIN intenta apertura; visitante solicita historial.

1. Guardar conteos de productos, ventas, turnos y lotes.
2. Solicitar las acciones ajenas por URL y POST válido con CSRF.
3. Comparar respuesta, cuerpo y conteos.

**Resultados esperados:** Roles ajenos reciben 403 y visitante redirección al ingreso; sin datos protegidos ni mutación de negocio. La ausencia del botón no es la única protección.

<a id="HU-AUTH-02"></a>

### HU-AUTH-02 · Autenticación — Bloquear cuenta por intentos fallidos

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como empleado o administrador, quiero que las cuentas se bloqueen temporalmente tras reiterados intentos fallidos de acceso, para proteger los accesos y las operaciones de la bodega.

**Reglas relacionadas:** RN-17. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 20.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-01; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-02-04](#contrato-DOC-02-04), [DOC-01-06](#contrato-DOC-01-06), [DEC-10-BLOQUEO-INACTIVIDAD](#contrato-DEC-10-BLOQUEO-INACTIVIDAD).

#### Criterios de aceptación

<a id="HU-AUTH-02-CA-01"></a>

**HU-AUTH-02/CA-01.** Dado que un usuario ingresa una contraseña incorrecta por quinta vez consecutiva, cuando se procesa el quinto intento fallido, entonces el sistema bloquea temporalmente la cuenta por 15 minutos conforme a la regla RN-17.

<a id="HU-AUTH-02-CA-02"></a>

**HU-AUTH-02/CA-02.** Dado que la cuenta se encuentra bajo bloqueo temporal, cuando se intenta ingresar nuevamente con cualquier clave, entonces el sistema impide el acceso y muestra en pantalla los minutos restantes del bloqueo.

<a id="HU-AUTH-02-CA-03"></a>

**HU-AUTH-02/CA-03.** Dado que transcurrió el tiempo de espera de 15 minutos, cuando el empleado ingresa sus credenciales válidas, entonces el sistema le permite ingresar exitosamente y restablece el contador de intentos a cero.

#### Casos de prueba escritos

<a id="CP-HU-AUTH-02-001"></a>
##### CP-HU-AUTH-02-001 · Quinto fallo, bloqueo compartido y expiración

**Cubre:** HU-AUTH-02/CA-01, HU-AUTH-02/CA-02, HU-AUTH-02/CA-03. **Estado:** VERIFICADO EN MUESTRA 01-F (14/11/2026) en secuencia, HTTP/Chrome y PostgreSQL 18.4 sobre build `2cef34b5...`; espera real de 15 min de reloj de pared no reejecutada en 01-F (ciclo previo heredado de 01-C con reserva de aislamiento).
**Evidencia de ejecución:** [01-F, matriz y límites](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-f) y [01-E](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-e). [postgresql-01f](auditoria_por_etapas/resultados/evidencias/01-F-20261114/postgresql-01f-latest.json) (`5/5` PASS en PG 18.4: `primera-fila`, `cinco-fallos`, `exito-antes-fallo` y `fallo-antes-exito` con espera en fila observada, más `admin-bypass-concurrente`), [chrome-manifest](auditoria_por_etapas/resultados/evidencias/01-F-20261114/chrome-manifest.json) (`C10/C11/C15`) y [security-probes](auditoria_por_etapas/resultados/evidencias/01-F-20261114/security-probes.json) (`DOC-01-04-ARGON2-BEFORE-LOCK-CHECK` INCUMPLE: Argon2 `check_password`/`set_password` corre antes de validar `locked_until > now`; `DOC-02-04-C03` CUMPLE en servicio). `/admin/login/` sigue sin compartir el bloqueo de `/`.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Cuenta vendedor.a; cuatro claves erróneas; quinta errónea a 10:00:00 Lima; otra sesión; reloj 10:14:59 y 10:15:00.

1. Enviar cuatro fallos y comprobar que todavía no bloquea por 15 min.
2. Enviar quinto; intentar clave correcta desde otro contexto a 10:14:59.
3. A10:15:00 ingresar correctamente.
4. Consultar contador.

**Resultados esperados:** Quinto fallo inicia bloqueo de 15 min compartido. Antes del vencimiento no ingresa e informa tiempo restante sin datos personales. Tras vencer ingresa; contador del flujo vuelve a 0. No extender plazo por cada intento bloqueado.

<a id="HU-AUTH-03"></a>

### HU-AUTH-03 · Salir de mi cuenta al terminar

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como empleado de la bodega, quiero salir de mi cuenta al terminar mi labor o ausentarme, para asegurar que nadie use mi sesión ni opere la caja en mi nombre.

**Reglas relacionadas:** RN-29, RN-30. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 2.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-02-04](#contrato-DOC-02-04), [DOC-01-06](#contrato-DOC-01-06).

#### Criterios de aceptación

<a id="HU-AUTH-03-CA-01"></a>

**HU-AUTH-03/CA-01.** Dado que tengo una sesión sin una venta en preparación, cuando elijo «Salir» y confirmo la advertencia de que un turno abierto seguirá ligado a mi usuario, entonces el sistema invalida la sesión y regresa a la pantalla de ingreso sin cerrar ese turno (RN-30).

<a id="HU-AUTH-03-CA-02"></a>

**HU-AUTH-03/CA-02.** Dado que mi venta en preparación contiene al menos una línea, cuando elijo «Salir», entonces el sistema advierte que descartará la venta; si confirmo, elimina todas las líneas sin afectar caja ni existencias y cierra la sesión, y si cancelo, conserva tanto la sesión como la venta (RN-30).

<a id="HU-AUTH-03-CA-03"></a>

**HU-AUTH-03/CA-03.** Dado que la salida fue confirmada, cuando se usa el botón Atrás o una URL anterior, entonces no se ve información del empleado ni se ejecutan operaciones sin autenticarse; si el mismo vendedor vuelve a ingresar, conserva su turno abierto pero no el borrador descartado, y otro vendedor no puede usar ni reemplazar ese turno.

#### Casos de prueba escritos

<a id="CP-HU-AUTH-03-001"></a>
##### CP-HU-AUTH-03-001 · Salida sin borrador y conservación del turno

**Cubre:** HU-AUTH-03/CA-01. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`) y Chrome real.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Variantes independientes: ADMIN sin turno; vendedor A con turno OPEN/apertura 100 y sin líneas.

1. Abrir Salir y leer advertencia.
2. Confirmar.
3. Reabrir navegador con la cookie previa y volver a ingresar como el mismo vendedor.

**Resultados esperados:** Sesión anterior invalida da. Advertencia solo afirma turno abierto cuando existe. Turno de A sigue OPEN con esperado 100; no se crea cierre. ADMIN no recibe texto que afirme turno propio inexistente.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Servidor 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="CP-HU-AUTH-03-002"></a>
##### CP-HU-AUTH-03-002 · Cancelar o confirmar salida con venta preparada

**Cubre:** HU-AUTH-03/CA-02, HU-AUTH-03/CA-03. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`), Chrome real y rollback atómico en PostgreSQL `18.4`.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Turno AOPEN; borrador 2Leche a 10; lotes A10/B10; apertura 100.

1. Elegir Salir y cancelar; comprobar sesión/líneas.
2. Repetir Salir y confirmar descarte.
3. Usar Atrás/URL anterior; ingresar de nuevo como A y luego como B.

**Resultados esperados:** Cancelar conserva 2 líneas/unidades y sesión. Confirmar elimina líneas activas/descarta borrador y revoca sesión sin ventas, stock 20 ni esperado 100 altera dos. Atrás no expone datos autenticados. A recupera turno sin borrador; B no lo ocupa ni abre paralelo.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [PostgreSQL 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="HU-AUTH-04a"></a>

### HU-AUTH-04a · Autenticación — Cerrar automáticamente la sesión previa

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como empleado, quiero que al iniciar sesión en un nuevo equipo se cierre automáticamente mi sesión anterior, para trabajar en un solo puesto a la vez y no dejar accesos abiertos.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01, HU-AUTH-03.

**Orden de producto:** 66.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-AUTH-04a-CA-01"></a>

**HU-AUTH-04a/CA-01.** Dado que tengo una sesión abierta en un equipo, cuando inicio sesión desde otro equipo con mis credenciales válidas, entonces la sesión previa se cierra de inmediato y solo queda habilitado el nuevo puesto.

<a id="HU-AUTH-04a-CA-02"></a>

**HU-AUTH-04a/CA-02.** Dado que mi sesión previa fue cerrada por inicio en otro equipo, cuando intento realizar cualquier acción desde ese puesto anterior, entonces la pantalla se bloquea y muestra «La sesión fue abierta en otro dispositivo».

<a id="HU-AUTH-04a-CA-03"></a>

**HU-AUTH-04a/CA-03.** Dado que la pantalla fue bloqueada, cuando intento interactuar con el puesto anterior, entonces el sistema me redirige a la pantalla de ingreso exigiendo escribir las credenciales.

#### Casos de prueba escritos

<a id="CP-HU-AUTH-04a-001"></a>
##### CP-HU-AUTH-04a-001 · Reemplazo de sesión en otro dispositivo

**Cubre:** HU-AUTH-04a/CA-01, HU-AUTH-04a/CA-02, HU-AUTH-04a/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; dos navegadores A/B para vendedor.a; sesión A activa.

1. Ingresar en B con misma cuenta.
2. Solicitar datos y enviar operación desde A.
3. Intentar continuar en A sin credenciales.

**Resultados esperados:** Solo B queda autorizada; A no lee ni escribe y muestra La sesión fue abierta en otro dispositivo antes de exigir ingreso. No conf und ir ocultar pantalla con revocar sesión. Caso no ejecutado: función futura.

<a id="HU-AUTH-04b"></a>

### HU-AUTH-04b · Autenticación — Descartar venta sin confirmar al cerrarse la sesión

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero que una venta sin confirmar se descarte si mi sesión se cierra por inicio en otro equipo, para que no queden cobros a medias ni se alteren las existencias o la caja.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-04a, HU-VEN-01b.

**Orden de producto:** 67.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-AUTH-04b-CA-01"></a>

**HU-AUTH-04b/CA-01.** Dado que tengo una venta en curso sin confirmar y mi sesión se cierra por inicio en otro equipo, cuando se procesa el cierre automático, entonces la venta incompleta se descarta y la lista de venta se libera.

<a id="HU-AUTH-04b-CA-02"></a>

**HU-AUTH-04b/CA-02.** Dado que se descarta una venta incompleta por cierre de sesión, cuando consulto las existencias de productos y el dinero en caja, entonces ambos permanecen iguales a su estado previo sin alteraciones.

#### Casos de prueba escritos

<a id="CP-HU-AUTH-04b-001"></a>
##### CP-HU-AUTH-04b-001 · Descarte por reemplazo sin efectos comerciales

**Cubre:** HU-AUTH-04b/CA-01, HU-AUTH-04b/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; sesión A con borrador 2Leche, stock 20 y caja 100; nueva sesión B.

1. Registrar stock/caja/ventas.
2. Ingresar en B provocando reemplazo de A.
3. Consultar borrador y repetir una petición de A.

**Resultados esperados:** Borrador anterior descartado y sin líneas cobrables; stock 20, caja 100, ventas 0. Petición de A denegada; reemplazo no confirma ni duplica venta. Depende de AUTH04 a.

<a id="HU-AUTH-05"></a>

### HU-AUTH-05 · Autenticación — Recuperar contraseña por correo

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como empleado, quiero recibir un código temporal en mi correo al olvidar mi clave, para restablecer mi acceso al sistema de forma segura sin depender de un administrador.

**Reglas relacionadas:** RN-17, RN-18, RN-24. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 68.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-AUTH-05-CA-01"></a>

**HU-AUTH-05/CA-01.** Dado que olvidé mi contraseña, cuando ingreso mi correo registrado en el formulario de recuperación, entonces el sistema despacha un código numérico temporal de 4 dígitos con validez de 15 minutos (RN-18).

<a id="HU-AUTH-05-CA-02"></a>

**HU-AUTH-05/CA-02.** Dado que recibí el código temporal, cuando lo ingreso dentro del tiempo de validez, entonces el sistema me permite definir una nueva contraseña que cumpla con los requisitos de seguridad de al menos 7 caracteres con mayúscula, minúscula y número (RN-24).

<a id="HU-AUTH-05-CA-03"></a>

**HU-AUTH-05/CA-03.** Dado que el código temporal fue utilizado exitosamente para cambiar la contraseña, cuando se intenta utilizar nuevamente el mismo código, entonces el sistema lo rechaza por haber expirado su único uso permitido (RN-18).

<a id="HU-AUTH-05-CA-04"></a>

**HU-AUTH-05/CA-04.** Dado que han transcurrido más de 15 minutos desde su emisión, cuando ingreso el código, entonces el sistema muestra el mensaje «El código ha caducado» y solicita generar uno nuevo.

<a id="HU-AUTH-05-CA-05"></a>

**HU-AUTH-05/CA-05.** Dado que una recuperación acumula 5 códigos erróneos consecutivos, cuando se intenta otro código, entonces el sistema suspende ese flujo durante 15 minutos sin bloquear por ello una sesión ya autenticada ni revelar si el correo existe (RN-17).

#### Casos de prueba escritos

<a id="CP-HU-AUTH-05-001"></a>
##### CP-HU-AUTH-05-001 · Código de recuperación válido y uso único

**Cubre:** HU-AUTH-05/CA-01, HU-AUTH-05/CA-02, HU-AUTH-05/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO pendiente de refinamiento de seguridad; buzón ficticio; código de fixture 4826 emitido 10:00; clave Nueva Segura 8!.

1. Solicitar recuperación en correo de prueba, usando backend de correo aislado.
2. A10:05 usar 4826 y nueva clave.
3. Intentar reutilizar 4826 con otra clave; probar login antiguo/nuevo.

**Resultados esperados:** Se emite un código al buzón ficticio, sin enviar lo a personas reales; primer uso cambia hash con política RN24 y consume código. Reutilización y clave antigua rechazadas; nueva clave ingresa. No publicar código en logs. No acredita seguridad de producción del diseño futuro.

<a id="CP-HU-AUTH-05-002"></a>
##### CP-HU-AUTH-05-002 · Caducidad y cinco códigos incorrectos

**Cubre:** HU-AUTH-05/CA-04, HU-AUTH-05/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; escenarios separados:4826 emitido 10:00 usado 10:15:01; cinco códigos 0000 incorrectos antes de caducar; sesión ya autenticada a parte.

1. Probar caducado.
2. Restaurar y fallar cinco veces el código; probar un sexto a 10:10.
3. Revisar sesión autenticada y respuesta para correo inexistente.

**Resultados esperados:** Caducado muestra El código ha caducado sin cambiar clave. Cinco fallos suspenden solo recuperación 15 min; no bloquean la sesión existente ni revelan existencia del correo. Stock/caja intactos.

<a id="HU-USR-01"></a>

### HU-USR-01 · Usuarios — Listar empleados del sistema

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** S. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero ver la lista de todos los empleados registrados con su estado y rol, para supervisar quién tiene acceso activo al sistema.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01 y cuentas iniciales.

**Orden de producto:** 22.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-USR-01-CA-01"></a>

**HU-USR-01/CA-01.** Dado que accedo a la sección de empleados, cuando la lista carga, entonces veo el nombre, correo, rol y estado (activo/inactivo) de cada empleado registrado.

<a id="HU-USR-01-CA-02"></a>

**HU-USR-01/CA-02.** Dado que la lista está cargada, cuando busco por nombre o correo, entonces el sistema filtra los resultados y muestra solo los empleados que coinciden.

<a id="HU-USR-01-CA-03"></a>

**HU-USR-01/CA-03.** Dado que la lista tiene varios registros, cuando la exploro, entonces puedo distinguir claramente cuáles cuentas están activas y cuáles inactivas.

#### Casos de prueba escritos

<a id="CP-HU-USR-01-001"></a>
##### CP-HU-USR-01-001 · Listado, búsqueda y estados de personal

**Cubre:** HU-USR-01/CA-01, HU-USR-01/CA-02, HU-USR-01/CA-03. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`) y Chrome real (`1366×768` y `390×844`).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Ana Caja/vendedor.a activo, Bruno Caja/vendedor.b activo e Inactivo Demo/inactivo@pruebas.invalid inactivo.

1. Abrir empleados.
2. Buscar Ana y luego vendedor.b@pruebas.invalid; limpiar búsqueda.
3. Revisar las columnas y estado de la cuenta inactiva.

**Resultados esperados:** Lista nombre, correo, rol exclusivo y estado; cada búsqueda devuelve solo coincidencias. Inactivo se distingue por texto, no solo color. No se exponen hash/clave.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [Servidor 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md).

<a id="HU-USR-02"></a>

### HU-USR-02 · Usuarios — Crear cuenta de nuevo empleado

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero registrar la cuenta de un nuevo trabajador con su correo único, rol y contraseña inicial, para permitir que el nuevo empleado acceda al sistema.

**Reglas relacionadas:** RN-12, RN-24. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 21.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-00-01](#contrato-DOC-00-01).

#### Criterios de aceptación

<a id="HU-USR-02-CA-01"></a>

**HU-USR-02/CA-01.** Dado que completo el formulario de nuevo empleado con nombre, correo, rol y contraseña inicial válida, cuando guardo el registro, entonces el empleado queda activo y puede iniciar sesión con esas credenciales.

<a id="HU-USR-02-CA-02"></a>

**HU-USR-02/CA-02.** Dado que ingreso un correo que ya existe en el sistema (activo o inactivo), cuando intento guardar, entonces el sistema muestra «El correo ya está registrado» y no permite duplicados (RN-12).

<a id="HU-USR-02-CA-03"></a>

**HU-USR-02/CA-03.** Dado que ingreso una contraseña inicial, cuando la valido, entonces el sistema verifica que tenga al menos 7 caracteres con mayúsculas, minúsculas y números, y rechaza la contraseña si no cumple ese criterio (RN-24).

<a id="HU-USR-02-CA-04"></a>

**HU-USR-02/CA-04.** Dado que el empleado fue creado, cuando finaliza el registro, entonces el sistema confirma su nombre, correo, estado activo y rol asignado.

#### Casos de prueba escritos

<a id="CP-HU-USR-02-001"></a>
##### CP-HU-USR-02-001 · Alta correcta y confirmación

**Cubre:** HU-USR-02/CA-01, HU-USR-02/CA-04. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`), Chrome real y registro transaccional `EMPLOYEE_CREATED`.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Camila Rojas, camila@pruebas.invalid, ALMACENERO, PruebaSegura9!.

1. Abrir alta; completar y guardar.
2. Leer confirmación y buscar la cuenta.
3. Ingresar en otro contexto con la cuenta nueva.

**Resultados esperados:** Una cuenta activa con nombre/correo/rol indicado; confirmación sin contraseña; ingreso permitido con opciones ALMACENERO. Correo único persistido normalizado.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [Servidor 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md).

<a id="CP-HU-USR-02-002"></a>
##### CP-HU-USR-02-002 · Correo duplicado y clave insuficiente

**Cubre:** HU-USR-02/CA-02, HU-USR-02/CA-03. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`) y carrera en PostgreSQL `18.4` (`duplicate_email_race`).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Variantes separadas: VENDEDOR.A@pruebas.invalid con espacios; correo de cuenta inactiva; clave abc, abcdefg, ABCDEFG, Abcdefg; correo nuevo válido.

1. Restaurar fixture antes de cada variante.
2. Enviar alta.
3. Comparar cuentas y errores asociados al campo.

**Resultados esperados:** Duplicados activos/inactivos muestran El correo ya está registrado; claves sin longitud/composición RN24 se rechazan. No se crea cuenta parcial ni se activa la inactiva.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Servidor 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md) · [PostgreSQL 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md).

<a id="HU-USR-03"></a>

### HU-USR-03 · Usuarios — Editar datos y rol de un empleado

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 8 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero modificar los datos personales y el rol asignado a un empleado, para mantener actualizado el directorio del personal y sus permisos de trabajo.

**Reglas relacionadas:** RN-12. **Dependencias funcionales:** HU-USR-02.

**Orden de producto:** 31.

**Estimación:** Cambio de rol, reset/desbloqueo explícito, revocación, invariantes y eventos.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-02-04](#contrato-DOC-02-04), [DOC-01-06](#contrato-DOC-01-06).

#### Criterios de aceptación

<a id="HU-USR-03-CA-01"></a>

**HU-USR-03/CA-01.** Dado que selecciono un empleado registrado, cuando accedo al formulario de edición, entonces puedo modificar su Nombre completo (nombres y apellidos juntos, hasta 120 caracteres, no único), correo electrónico y su rol de trabajo en el sistema.

<a id="HU-USR-03-CA-02"></a>

**HU-USR-03/CA-02.** Dado que modifico el correo electrónico del empleado, cuando intento guardar, entonces el sistema valida que el nuevo correo no se encuentre registrado previamente por otro trabajador (RN-12).

<a id="HU-USR-03-CA-03"></a>

**HU-USR-03/CA-03.** Dado que cambio el rol del empleado, cuando confirmo la modificación, entonces el nuevo rol queda registrado y aplica de inmediato.

#### Casos de prueba escritos

<a id="CP-HU-USR-03-001"></a>
##### CP-HU-USR-03-001 · Editar nombre, correo y rol

**Cubre:** HU-USR-03/CA-01, HU-USR-03/CA-03. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`) y Chrome real.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; empleado Bsin turno; Nombre completo de 120 caracteres; nuevo@pruebas.invalid; rol ALMACENERO.

1. Editar y guardar.
2. Refrescar lista.
3. Intentar operación de antiguo VENDEDOR y nueva operación permitida con sesión revalida da.

**Resultados esperados:** Nombre completo único campo (homónimos permitidos), correo/rol actualizados; permisos cambian sin ventana de privilegio anterior. No cambia historia de ventas ni autorías.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Servidor 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="CP-HU-USR-03-002"></a>
##### CP-HU-USR-03-002 · Rechazos de edición y bloqueo comercial

**Cubre:** HU-USR-03/CA-02. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor aislado (`652/652`), Chrome real (`role_change_open_shift_blocked_ui`) y carrera en PostgreSQL `18.4` (`open_shift_vs_role_change`).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Variantes independientes: correo de A; nombre 121 caracteres; cambiar rol vendedor Acon turno OPEN; degradar único ADMIN.

1. Registrar estado cuenta/turno/sesiones.
2. Enviar cada edición.
3. Comparar estado tras respuesta.

**Resultados esperados:** Duplicado/error de longitud y operaciones que dejan turno sin responsable o sin ADMIN se rechazan sin mutación. No limpiar bloqueo de cuenta por cambiar correo. Reset/desbloqueo requiere su contrato explícito.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [PostgreSQL 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="HU-USR-04"></a>

### HU-USR-04 · Usuarios — Desactivar cuenta de empleado

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero desactivar la cuenta de un empleado que ya no trabaja en la bodega, para impedir su acceso al sistema.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-USR-01.

**Orden de producto:** 23.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-02-04](#contrato-DOC-02-04).

#### Criterios de aceptación

<a id="HU-USR-04-CA-01"></a>

**HU-USR-04/CA-01.** Dado que selecciono desactivar la cuenta de un empleado activo, cuando confirmo la acción, entonces el empleado queda con estado Inactivo y no puede ingresar al sistema.

<a id="HU-USR-04-CA-02"></a>

**HU-USR-04/CA-02.** Dado que una cuenta de empleado fue desactivada, cuando intenta ingresar al sistema, entonces el sistema muestra el mismo mensaje general «Correo o contraseña incorrectos» que en HU-AUTH-01, sin revelar el estado de la cuenta.

<a id="HU-USR-04-CA-03"></a>

**HU-USR-04/CA-03.** Dado que desactivé una cuenta, cuando la busco en la lista, entonces aparece con estado Inactivo y el historial de operaciones del empleado se conserva.

#### Casos de prueba escritos

<a id="CP-HU-USR-04-001"></a>
##### CP-HU-USR-04-001 · Confirmar desactivación, negar acceso y conservar historia

**Cubre:** HU-USR-04/CA-01, HU-USR-04/CA-02, HU-USR-04/CA-03. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con confirmación intermedia `/empleados/<id>/estado/confirmar/`, servidor (`652/652`), Chrome real (`state_confirm_*`, expulsión multi-navegador) y carrera `last_admin_race` en PostgreSQL `18.4`.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; vendedor Bactivo sin turno OPEN, venta histórica V-00000002 y sesión B.

1. Abrir desactivación y cancelar; comprobar estado.
2. Reabrir, revisar impacto y confirmar.
3. Usar cookie B y credenciales B; consultar lista e historia con ADMIN.

**Resultados esperados:** Cancelar no modifica. Confirmar deja Inactivo y revoca acceso; login muestra mensaje general. Historia y referencias se conservan, cuenta sigue en listado. No desactivar último ADMIN ni dueño de turno abierto mediante atajo.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [PostgreSQL 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="HU-USR-05"></a>

### HU-USR-05 · Usuarios — Reactivar cuenta de empleado

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero reactivar la cuenta de un empleado que regresó al negocio, para restaurar su acceso sin necesidad de crear una cuenta nueva.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-USR-04.

**Orden de producto:** 32.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-02-04](#contrato-DOC-02-04).

#### Criterios de aceptación

<a id="HU-USR-05-CA-01"></a>

**HU-USR-05/CA-01.** Dado que selecciono reactivar la cuenta de un empleado inactivo, cuando confirmo la acción, entonces la cuenta queda Activa y puede ingresar con sus credenciales habituales si no subsiste un bloqueo u otra restricción; reactivar no limpia el bloqueo ni revive sesiones revocadas (RN-17).

<a id="HU-USR-05-CA-02"></a>

**HU-USR-05/CA-02.** Dado que reactivé una cuenta, cuando el empleado ingresa, entonces accede al sistema con el mismo rol y permisos que tenía antes de la desactivación.

#### Casos de prueba escritos

<a id="CP-HU-USR-05-001"></a>
##### CP-HU-USR-05-001 · Reactivar preservando rol, sin revivir cookie

**Cubre:** HU-USR-05/CA-01, HU-USR-05/CA-02. **Estado:** EJECUTADO Y VERIFICADO en sublote 02-E (segunda pasada acotada, 14/11/2026) con servidor (`652/652`), Chrome real (`reactivate_confirm_shows_lockout_warning`, `lockout_survived_rename_and_reactivate`, `explicit_unlock_allows_login`) y PostgreSQL `18.4` (`lockout_preservation_pg`).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; vendedor B inactivo sin bloqueo temporal vigente; cookie antigua revoca da.

1. Revisar reactivación y confirmar.
2. Probar cookie anterior y luego ingreso nuevo con credenciales habituales.
3. Repetir con bloqueo temporal aún vigente.

**Resultados esperados:** Estado Activo y rol VENDEDOR conservados; cookie vieja sigue inválida. Login nuevo válido cuando no hay sanción; con bloqueo vigente se respeta su plazo o desbloqueo ADMIN explícito auditado. No reset silencioso.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [PostgreSQL 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="HU-USR-06"></a>

### HU-USR-06 · Usuarios — Forzar cierre de sesión remoto

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero cerrar de forma remota la sesión activa de cualquier empleado, para proteger el sistema ante situaciones imprevistas o abandono de puesto.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-USR-01 y HU-AUTH-01.

**Orden de producto:** 69.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-USR-06-CA-01"></a>

**HU-USR-06/CA-01.** Dado que un empleado tiene sesión abierta, cuando selecciono «Cerrar sesión» desde la pantalla de administración, entonces el empleado es desconectado de forma inmediata.

<a id="HU-USR-06-CA-02"></a>

**HU-USR-06/CA-02.** Dado que su sesión fue cerrada remotamente, cuando el empleado intenta continuar navegando, entonces el sistema le muestra la pantalla de ingreso con el mensaje «Tu sesión fue cerrada por el administrador».

#### Casos de prueba escritos

<a id="CP-HU-USR-06-001"></a>
##### CP-HU-USR-06-001 · Revocación remota explícita

**Cubre:** HU-USR-06/CA-01, HU-USR-06/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN y dos sesiones de B; B con turno OPEN y sin cobro en vuelo.

1. ADMIN selecciona cerrar sesiones de B.
2. Desde ambas cookies consultar/operar.
3. Consultar estado de cuenta y turno.

**Resultados esperados:** Las sesiones objetivo se revocan y muestran Tu sesión fue cerrada por el administrador al intentar continuar; cuenta no se desactiva y turno no se cierra. Definir carrera con cobro antes de implementar.

<a id="HU-LOG-01"></a>

### HU-LOG-01 · Supervisión de accesos – Consultar registro de accesos

**Épica:** EPIC-SEG. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero consultar el historial de ingresos y salidas del sistema de todos los empleados, para supervisar los accesos y detectar actividad inusual.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01 y HU-AUTH-02.

**Orden de producto:** 70.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-02; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-01-06](#contrato-DOC-01-06).

#### Criterios de aceptación

<a id="HU-LOG-01-CA-01"></a>

**HU-LOG-01/CA-01.** Dado que accedo al registro de accesos, cuando la lista carga, entonces veo por cada evento: nombre del empleado, tipo de evento (ingreso o salida) y fecha con hora exacta.

<a id="HU-LOG-01-CA-02"></a>

**HU-LOG-01/CA-02.** Dado que consulto el registro, cuando filtro por empleado o por rango de fechas, entonces el sistema muestra únicamente los eventos que coinciden con el filtro.

<a id="HU-LOG-01-CA-03"></a>

**HU-LOG-01/CA-03.** Dado que ocurrió un bloqueo de cuenta por intentos fallidos, cuando lo busco en el registro, entonces aparece como un evento diferenciado.

#### Casos de prueba escritos

<a id="CP-HU-LOG-01-001"></a>
##### CP-HU-LOG-01-001 · Consultar eventos y filtrar sin secretos

**Cubre:** HU-LOG-01/CA-01, HU-LOG-01/CA-02, HU-LOG-01/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; eventos Ana ingreso 09:00/salida 09:30/bloqueo 10:00 y Bruno ingreso 11:00 del 12 nov.

1. ADMIN abre registro.
2. Filtrar Ana y 09:45–10:15.
3. Abrir bloqueo y examinar campos; VENDEDOR solicita ruta.

**Resultados esperados:** Lista actor/tipo/fecha Lima; filtro deja bloqueo Ana 10:00 y lo diferencia de ingreso/salida. No expone clave/cookie/CSRF; VENDEDOR denegado. Bitácora UI futura no exime eventos técnicos actuales.

<a id="EPIC-CAT"></a>

## EPIC-CAT · Productos y proveedores

<a id="HU-CAT-01"></a>

### HU-CAT-01 · Categorías — Ver lista de categorías de productos

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** S. **Puntos Fibonacci:** 1 (orientativos; anteriores:1).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero ver la lista completa de categorías registradas, para conocer cómo está organizado el catálogo antes de registrar o modificar productos.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01 y datos iniciales de categoría.

**Orden de producto:** 11.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [PROP-E00-HU-02](#contrato-PROP-E00-HU-02).

#### Criterios de aceptación

<a id="HU-CAT-01-CA-01"></a>

**HU-CAT-01/CA-01.** Dado que accedo a la sección de categorías, cuando la lista carga, entonces veo el nombre de cada categoría registrada.

<a id="HU-CAT-01-CA-02"></a>

**HU-CAT-01/CA-02.** Dado que no hay ninguna categoría registrada, cuando accedo a la sección, entonces el sistema muestra un mensaje indicando que la lista está vacía.

#### Casos de prueba escritos

<a id="CP-HU-CAT-01-001"></a>
##### CP-HU-CAT-01-001 · Lista poblada y vacía

**Cubre:** HU-CAT-01/CA-01, HU-CAT-01/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; escenarios separados categorías Lácteos activa y Bebidas inactiva; base sin categorías.

1. Consultar categorías con dos filas.
2. Restaurar base vacía y consultar.

**Resultados esperados:** Nombres/estados correctos; vacía muestra mensaje de ausencia, no error 500 ni tabla ficticia. No crear categorías al hacer GET.

<a id="HU-CAT-02"></a>

### HU-CAT-02 · Categorías — Crear nueva categoría de productos

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** S. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador de la bodega, quiero registrar una nueva categoría de productos, para organizar los artículos y facilitar su localización en el inventario.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 10.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [PROP-E00-HU-02](#contrato-PROP-E00-HU-02).

#### Criterios de aceptación

<a id="HU-CAT-02-CA-01"></a>

**HU-CAT-02/CA-01.** Dado que ingreso un nombre de categoría no vacío, cuando confirmo el registro, entonces el sistema retira espacios sobrantes, guarda la categoría con estado activo y la deja disponible para usos posteriores en el catálogo.

<a id="HU-CAT-02-CA-02"></a>

**HU-CAT-02/CA-02.** Dado que ya existe una categoría registrada con el mismo nombre aunque cambien mayúsculas o espacios, cuando intento guardar, entonces el sistema muestra el mensaje «La categoría ya existe» y no crea un duplicado.

<a id="HU-CAT-02-CA-03"></a>

**HU-CAT-02/CA-03.** Dado que el nombre queda vacío al retirar espacios, cuando intento guardar, entonces el sistema indica «El nombre es obligatorio» y no registra la categoría.

#### Casos de prueba escritos

<a id="CP-HU-CAT-02-001"></a>
##### CP-HU-CAT-02-001 · Alta normaliza da y rechazo de duplicado/vacío

**Cubre:** HU-CAT-02/CA-01, HU-CAT-02/CA-02, HU-CAT-02/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; nombres independientes:  Lácteos  , lácteos, espacios únicamente; categoría Lácteos ya existe para duplicado.

1. Crear primera categoría.
2. Intentar segunda con distinto uso de mayúsculas/espacios.
3. Intentar nombre vacío trastrim.

**Resultados esperados:** Primera guarda Lácteos activa; duplicado muestra La categoría ya existe y no agrega fila; vacío El nombre es obligatorio. Categoría activa se ofrece al registrar producto.

<a id="HU-CAT-03"></a>

### HU-CAT-03 · Categorías — Editar nombre de categoría

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 1 (orientativos; anteriores:1).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero modificar el nombre de una categoría registrada, para corregir errores de escritura o actualizar su denominación.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-CAT-02.

**Orden de producto:** 71.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CAT-03-CA-01"></a>

**HU-CAT-03/CA-01.** Dado que edito el nombre de una categoría con un texto nuevo y único, cuando guardo, entonces el cambio se refleja en la lista y en todos los productos pertenecientes a ella.

<a id="HU-CAT-03-CA-02"></a>

**HU-CAT-03/CA-02.** Dado que edito el nombre con una denominación que ya pertenece a otra categoría, cuando intento guardar, entonces el sistema muestra «La categoría ya existe» y no realiza el cambio.

#### Casos de prueba escritos

<a id="CP-HU-CAT-03-001"></a>
##### CP-HU-CAT-03-001 · Renombrar categoría conservando relaciones

**Cubre:** HU-CAT-03/CA-01, HU-CAT-03/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; Lácteos con producto Leche; Bebidas existente.

1. Cambiar Lácteos por Lácteos y derivados.
2. Consultar Leche.
3. Intentar renombrar a Bebidas.

**Resultados esperados:** Primer cambio visible en catálogo y productos sin cambiar su identidad/stock. Segundo rechaza La categoría ya existe y conserva nombre anterior.

<a id="HU-CAT-04"></a>

### HU-CAT-04 · Categorías — Eliminar categoría sin productos

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero eliminar una categoría que no tiene productos asociados, para mantener el catálogo limpio y sin grupos vacíos.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-CAT-02 y HU-PROD-01.

**Orden de producto:** 72.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CAT-04-CA-01"></a>

**HU-CAT-04/CA-01.** Dado que selecciono eliminar una categoría que no tiene productos asociados, cuando confirmo la acción, entonces la categoría desaparece de la lista.

<a id="HU-CAT-04-CA-02"></a>

**HU-CAT-04/CA-02.** Dado que selecciono eliminar una categoría que tiene productos vinculados, cuando intento confirmar, entonces el sistema muestra «No se puede eliminar: esta categoría tiene productos registrados» y cancela la acción.

#### Casos de prueba escritos

<a id="CP-HU-CAT-04-001"></a>
##### CP-HU-CAT-04-001 · Eliminar solo categoría sin productos

**Cubre:** HU-CAT-04/CA-01, HU-CAT-04/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; Vacía sin productos; Lácteos con Leche, incluso si Leche está inactiva.

1. Confirmar eliminación Vacía.
2. Intentar eliminar Lácteos.

**Resultados esperados:** Vacía desaparece; Lácteos se conserva con mensaje No se puede eliminar: esta categoría tiene productos registrados. No borrar producto, lote ni historia en cascada.

<a id="HU-PROD-01"></a>

### HU-PROD-01 · Productos — Ver catálogo completo de productos

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o almacenero, quiero ver la lista completa de productos registrados con su precio y existencias, para conocer la disponibilidad de cada artículo antes de operar. El vendedor consulta productos únicamente en su flujo de venta autorizado (RN-29; conciliación DOC-00-14, 09/11/2026).

**Reglas relacionadas:** RN-06. **Dependencias funcionales:** HU-PROD-02.

**Orden de producto:** 12.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-12-PERMISOS-HISTORIAL-Y-MENU](#contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU), [DEC-07-VENCIDOS-FILTRO](#contrato-DEC-07-VENCIDOS-FILTRO).

#### Criterios de aceptación

<a id="HU-PROD-01-CA-01"></a>

**HU-PROD-01/CA-01.** Dado que accedo al catálogo de productos, cuando la lista carga, entonces veo por cada artículo: nombre, código de barras, categoría, precio de venta y existencias disponibles.

<a id="HU-PROD-01-CA-02"></a>

**HU-PROD-01/CA-02.** Dado que consulto el catálogo, cuando busco por nombre o código de barras, entonces el sistema filtra los resultados y muestra solo los artículos coincidentes.

<a id="HU-PROD-01-CA-03"></a>

**HU-PROD-01/CA-03.** Dado que un producto tiene existencias iguales o inferiores al mínimo configurado (RN-06), cuando aparece en la lista, entonces muestra una señal visual de alerta.

#### Casos de prueba escritos

<a id="CP-HU-PROD-01-001"></a>
##### CP-HU-PROD-01-001 · Catálogo, búsqueda y alerta coherente

**Cubre:** HU-PROD-01/CA-01, HU-PROD-01/CA-02, HU-PROD-01/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN/ALMACENERO; Leche códigoINT-LECHE-1 precio 10 stock vendible 20 mínimo 10; Arroz códigoINT-ARROZ-1 precio 5 stock vendible 5 mínimo 10; Arroz inactivo en variante.

1. Consultar catálogo en cada rol.
2. Buscar Leche yINT-ARROZ-1.
3. Consultar umbral y variante inactiva; VENDEDOR solicita catálogo directo.

**Resultados esperados:** Columnas nombre/código/categoría/precio/existencias numéricas; filtros dejan coincidencia. Arroz activo 5<=10 alerta; inactivo se identifica y no se ofrece como demanda de reposición. VENDEDOR denegado, consulta desde POS sin costos.

<a id="HU-PROD-02"></a>

### HU-PROD-02 · Registrar un producto por unidad con vencimiento

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador de la bodega, quiero registrar un producto de cualquier categoría activa, por unidad y con vencimiento obligatorio, para incorporarlo al catálogo y controlar sus existencias (alcance actual aceptado en DOC03-01, 09/11/2026).

**Reglas relacionadas:** RN-06, RN-27, RN-29. **Dependencias funcionales:** HU-AUTH-01; categoría activa existente (CAT02 o datos iniciales).

**Orden de producto:** 3.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-11-TOPE-EFECTIVO-FORM](#contrato-DEC-11-TOPE-EFECTIVO-FORM), [DOC-00-01](#contrato-DOC-00-01).

#### Criterios de aceptación

<a id="HU-PROD-02-CA-01"></a>

**HU-PROD-02/CA-01.** Dado que ingreso con rol `ADMIN` y existe una categoría activa, cuando la elijo y registro nombre único ignorando mayúsculas y espacios redundantes, código de barras, unidad `UND`, precio con IGV incluido y cantidad mínima válidos, entonces el producto queda asociado a esa categoría, sea o no de enlatados, y con control de vencimiento obligatorio; una categoría inactiva o inexistente se rechaza sin crear producto (RN-03, RN-29; DOC03-01, 09/11/2026).

<a id="HU-PROD-02-CA-02"></a>

**HU-PROD-02/CA-02.** Dado que registro el precio de venta en soles, cuando el sistema lo valida, entonces exige un valor mayor que cero con máximo dos decimales y lo interpreta como precio final con IGV incluido (RN-27).

<a id="HU-PROD-02-CA-03"></a>

**HU-PROD-02/CA-03.** Dado que indico un código de barras que ya pertenece a otro producto, cuando intento guardar, entonces el sistema rechaza el registro por ser un código irrepetible.

<a id="HU-PROD-02-CA-04"></a>

**HU-PROD-02/CA-04.** Dado que indico la cantidad mínima de existencias, cuando guardo, entonces acepta un entero entre 0 y 999999 inclusive, tanto en formulario como en servidor; si no ingreso el campo al registrar, almacena 10. Un valor fuera del rango se rechaza sin guardar cambios, y el alcance vigente aplica alertas coherentes con RN-06 (PROP-03C-LIMITES ratificada por delegación el12/11/2026; la procedencia anterior se conserva en BASELINE).

<a id="HU-PROD-02-CA-05"></a>

**HU-PROD-02/CA-05.** Dado que todos los datos son válidos, cuando se confirma el registro, entonces el producto se crea con cero existencias y no resulta vendible hasta recibir lotes; si un `ALMACENERO` o `VENDEDOR` intenta registrar por acceso directo, el sistema deniega la operación y no crea ningún producto (RN-29).

#### Casos de prueba escritos

<a id="CP-HU-PROD-02-001"></a>
##### CP-HU-PROD-02-001 · Alta UND y estado inicial

**Cubre:** HU-PROD-02/CA-01, HU-PROD-02/CA-02, HU-PROD-02/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Lácteos activa, Yogur natural 200 g, internoINT-YOGUR-200, UND, precio 2.50, min 10.

1. Crear producto.
2. Revisar categoría/unidad/vencimiento obligatorio/precio.
3. Consultar stock y buscarlo en POS sin lotes.

**Resultados esperados:** Un producto activo de categoría elegida, precio 2.50 con IGV incluido, stock 0 y no vendible; ningún lote/venta/caja crea dos. No exigir categoría enlatados.

<a id="CP-HU-PROD-02-002"></a>
##### CP-HU-PROD-02-002 · Unicidad, mínimos y denegación

**Cubre:** HU-PROD-02/CA-03, HU-PROD-02/CA-04, HU-PROD-02/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Variantes independientes: códigoINT-LECHE-1 repetido; mínimo omitido/0/999999/1000000/-1/1.5; precio 0/2.501; categoría inactiva; actor ALMACENERO.

1. En cada variante partir de ficha nueva distinta.
2. Enviar registro y consultar filas.
3. Contrastar formulario y POST alterado.

**Resultados esperados:** Código repetido rechazado; mínimo omitido 10,0 y 999999 válidos, otros inválidos. Precio 0/exceso precisión y categoría inactiva rechazan; actor no ADMIN403. Ningún rechazo crea producto. No duplicar nombre comercial normalizado.

<a id="HU-PROD-03"></a>

### HU-PROD-03 · Productos — Escanear código de barras para registrar producto

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** C. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero capturar el código de barras de un producto nuevo con el lector, para registrar su código en el formulario de forma rápida y sin errores de digitación.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-PROD-02.

**Orden de producto:** 33.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-PROD-03-CA-01"></a>

**HU-PROD-03/CA-01.** Dado que abro «Escanear código» en el alta de producto, cuando leo una etiqueta, entonces «Código leído» muestra automáticamente el valor temporal. Al pulsar «Usar código», se copia a la ficha para confirmarlo con «Registrar producto».

<a id="HU-PROD-03-CA-02"></a>

**HU-PROD-03/CA-02.** Dado que el código leído ya existe en el catálogo, cuando se detecta la lectura, entonces el sistema advierte «El código de barras ya está registrado» e impide duplicarlo.

#### Casos de prueba escritos

<a id="CP-HU-PROD-03-001"></a>
##### CP-HU-PROD-03-001 · Captura revisa da y código ya reservado

**Cubre:** HU-PROD-03/CA-01, HU-PROD-03/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; GTIN existente 4006381333931; código interno nuevo 000123.

1. Abrir Escanear código.
2. Leer 4006381333931 y revisar campo temporal.
3. Intentar Usar código duplicado; luego capturar interno 000123 en alta nueva.
4. Pulsar Usar código; confirmar ficha expresamente.

**Resultados esperados:** Lectura llena temporal sin enviar ficha. Duplicado impide copia y explica conflicto; código interno conserva ceros. Usar código copia, Registrar producto guarda. Falla de red informa que no se pudo comprobar; servicio revalida unicidad al guardar.

<a id="HU-PROD-04"></a>

### HU-PROD-04 · Productos — Editar datos de un producto

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero modificar el nombre, código de barras, precio, categoría o cantidad mínima de un producto registrado, para mantener actualizada la información de los artículos (corrección de código aceptada en DOC03-02, 09/11/2026).

**Reglas relacionadas:** RN-06. **Dependencias funcionales:** HU-PROD-02.

**Orden de producto:** 13.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-00-01](#contrato-DOC-00-01).

#### Criterios de aceptación

<a id="HU-PROD-04-CA-01"></a>

**HU-PROD-04/CA-01.** Dado que edito el precio de venta de un producto, cuando guardo, entonces el nuevo precio aplica a las ventas registradas a partir de ese momento; las ventas pasadas conservan el precio cobrado.

<a id="HU-PROD-04-CA-02"></a>

**HU-PROD-04/CA-02.** Dado que edito la cantidad mínima de un producto, cuando guardo, entonces el umbral de alerta se actualiza de inmediato (RN-06).

<a id="HU-PROD-04-CA-03"></a>

**HU-PROD-04/CA-03.** Dado que ingreso como `ADMIN`, cuando corrijo el código de barras de un producto, entonces se exige un código normalizado único, se conserva la identidad del producto y sus referencias, y las ventas pasadas mantienen sus datos históricos; un código duplicado o inválido se rechaza sin guardar cambios (DOC03-02, decisión del usuario del 09/11/2026; RN-28, RN-29).

<a id="HU-PROD-04-CA-04"></a>

**HU-PROD-04/CA-04.** Dado que edito el nombre de un producto con una descripción válida, cuando guardo, entonces el nuevo nombre se actualiza en el catálogo y en la pantalla de venta; debe ser único entre productos activos e inactivos, ignorando mayúsculas y espacios redundantes, y conserva los datos de ventas pasadas. Un duplicado se rechaza sin guardar ningún cambio; marca, contenido o presentación distinguen productos diferentes (PROP-03C-NOMBRE ratificada por delegación, 12/11/2026).

<a id="HU-PROD-04-CA-05"></a>

**HU-PROD-04/CA-05.** Dado que reasigno la categoría de un producto, cuando confirmo el cambio, entonces el producto queda reclasificado en la nueva categoría.

#### Casos de prueba escritos

<a id="CP-HU-PROD-04-001"></a>
##### CP-HU-PROD-04-001 · Editar datos sin romper historia

**Cubre:** HU-PROD-04/CA-01, HU-PROD-04/CA-02, HU-PROD-04/CA-03, HU-PROD-04/CA-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Leche con venta histórica 2×10 y snapshot nombre/código; nuevo precio 11.50, min 12, nombre Leche entera 1L, códigoINT-LECHE-NUEVO, categoría activa.

1. Editar precio/mínimo/nombre/categoría/código y guardar.
2. Consultar ficha/POS/venta antigua/Kardex.
3. Intentar código o nombre normalizado de otra ficha y categoría inactiva.

**Resultados esperados:** Ficha y oferta nuevas muestran 11.50/min 12/nombre/código actuales con misma ID. Venta antigua sigue 2×10 y snapshots originales; Kardex sigue enlazado. Conflictos rechazan sin cambios. Nombres únicos también entre inactivos; no quitar acentos.

<a id="CP-HU-PROD-04-002"></a>
##### CP-HU-PROD-04-002 · Reclasificación con borrador abierto

**Cubre:** HU-PROD-04/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; borrador Acon 1Leche de Lácteos; otra categoría activa Abarrotes.

1. Mover Leche de Lácteos a Abarrotes sin cambiar precio/código/estado.
2. Volver al borrador y cobrar según contrato vigente.

**Resultados esperados:** Reclasificación entre categorías activas conserva identidad/historia y permite operación si producto sigue vendible. Si cambia precio/estado se aplica revisión/rechazo correspondiente; no decidir por texto obsoleto de pestaña.

<a id="HU-PROD-05"></a>

### HU-PROD-05 · Productos — Gestionar estado de disponibilidad comercial

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero cambiar el estado de un producto entre Activo e Inactivo, para suspender temporalmente su venta sin borrarlo o volver a habilitarlo.

**Reglas relacionadas:** RN-03 para existencias vigentes y RN-29 para los permisos de cada rol.. **Dependencias funcionales:** HU-PROD-02.

**Orden de producto:** 14.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-03; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-07-VENCIDOS-FILTRO](#contrato-DEC-07-VENCIDOS-FILTRO), [PROP-E00-HU-02](#contrato-PROP-E00-HU-02).

#### Criterios de aceptación

<a id="HU-PROD-05-CA-01"></a>

**HU-PROD-05/CA-01.** Dado que cambio el estado de un producto a «Inactivo», cuando un vendedor intenta buscarlo en mostrador, entonces el producto queda excluido de la venta.

<a id="HU-PROD-05-CA-02"></a>

**HU-PROD-05/CA-02.** Dado que el administrador reactiva un producto, cuando el vendedor con turno propio abierto lo busca en mostrador, entonces aparece con su precio de venta actual y la suma de unidades de lotes vigentes si la categoría está activa y esa suma es positiva. Solo cuentan los lotes que vencen después de hoy en Lima (RN-03). Con categoría desactivada o cero unidades vigentes, la ficha queda activa, el catálogo indica el motivo y el mostrador la excluye.

<a id="HU-PROD-05-CA-03"></a>

**HU-PROD-05/CA-03.** Dado que un producto se encuentra inactivo, cuando el administrador revisa el catálogo, entonces se muestra con la etiqueta «Inactivo» y conserva todo su historial.

#### Casos de prueba escritos

<a id="CP-HU-PROD-05-001"></a>
##### CP-HU-PROD-05-001 · Suspender y reactivar disponibilidad

**Cubre:** HU-PROD-05/CA-01, HU-PROD-05/CA-02, HU-PROD-05/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Leche activa con 20 unidades, borrador Acon 1; variante categoría inactiva.

1. Enviar destino Deshabilitar y repetir mismo destino.
2. Buscar/agregar/cobrar Leche.
3. Habilitar producto y consultar variante de categoría inactiva.

**Resultados esperados:** Estado explícito no alterna al repetir. Deshabilitada no se ofrece ni cobra; stock/historia intactos. Reactivada solo ven de si categoría activa y lote vigente. Categoría inactiva sigue bloqueando, sin activar productos indirectamente.

<a id="HU-PROD-06"></a>

### HU-PROD-06 · Productos — Consultar vencimientos de productos

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o encargado del almacén, quiero consultar la lista de productos cuyos lotes vencen próximamente, para tomar decisiones de baja o rotación antes de que caduquen.

**Reglas relacionadas:** RN-03. **Dependencias funcionales:** HU-INV-01a.

**Orden de producto:** 15.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-07; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-07-VENCIDOS-FILTRO](#contrato-DEC-07-VENCIDOS-FILTRO).

#### Criterios de aceptación

<a id="HU-PROD-06-CA-01"></a>

**HU-PROD-06/CA-01.** Dado que accedo a la consulta de vencimientos, cuando la lista carga, entonces veo los productos ordenados de menor a mayor días restantes de vida útil, mostrando nombre, número de lote y fecha de caducidad.

<a id="HU-PROD-06-CA-02"></a>

**HU-PROD-06/CA-02.** Dado que un lote ya venció por tener fecha igual o anterior a hoy según la hora de Lima, cuando aparece en la lista, entonces figura marcado como «Vencido» y bloqueado para venta (RN-03).

<a id="HU-PROD-06-CA-03"></a>

**HU-PROD-06/CA-03.** Dado que consulto la lista, cuando filtro por número de días (por ejemplo próximos 7 días), entonces solo aparecen los lotes cuyo vencimiento se ubica dentro de ese plazo.

#### Casos de prueba escritos

<a id="CP-HU-PROD-06-001"></a>
##### CP-HU-PROD-06-001 · Ventanas y vencidos con fecha Lima

**Cubre:** HU-PROD-06/CA-01, HU-PROD-06/CA-02, HU-PROD-06/CA-03. **Estado:** EJECUTADO PARCIAL en primera pasada (`07-B`, 14/11/2026 Lima): `HU-PROD-06/CA-01` y `CA-02` CUMPLE en muestra aislada, Chrome y PostgreSQL `18.4`; `HU-PROD-06/CA-03` INCUMPLE porque `?dias=7` mezcla vencidos y próximos en una tabla única sin separar ni excluir vencidos (`r1-pmv` `f0d6fa81...` / `c7bfe1fa...`).
**Evidencia de ejecución:** [Informe 07-B y límites](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Inventario y disposiciones 07-B](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md) · [Sondas 07-B](auditoria_por_etapas/resultados/evidencias/07-B-20261114/probes-07b.json) · [Chrome 07-B](auditoria_por_etapas/resultados/evidencias/07-B-20261114/browser-07b-summary.json) · [PG 18.4 07](auditoria_por_etapas/resultados/evidencias/07-postgresql-20261115T025829083471Z.json).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** 12 nov Lima; lote A vence 13 nov/10 unidades, B12 dic/10, E12 nov/3. Filtros 1,30,3650,0,3651, abc; producto E inactivo en variante.

1. Consultar vencimientos próximos y vencidos.
2. Cambiar días y repetir variantes inválidas.
3. Revisar días restantes/stock/badges y la medianoche Lima con reloj controlado.

**Resultados esperados:** Próximos 1 día incluye A; 30 días A/B; vencidos incluye E, también inactivo con badge. Hoy cuenta vencido/no vendible. Rango 1..3650; inválido informa y usa 30. Fechas/días/coincidencias correctos, sin 500.

<a id="HU-PROV-01"></a>

### HU-PROV-01 · Proveedores — Ver lista de proveedores

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** S. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o encargado del almacén, quiero ver la lista de todos los proveedores registrados con su estado, para conocer los contactos disponibles para pedidos de mercadería.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 28.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-04; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-04-RUC-VALIDACION](#contrato-DEC-04-RUC-VALIDACION).

#### Criterios de aceptación

<a id="HU-PROV-01-CA-01"></a>

**HU-PROV-01/CA-01.** Dado que accedo a la sección de proveedores, cuando la lista carga, entonces veo el nombre comercial, RUC y estado (activo/inactivo) de cada proveedor.

<a id="HU-PROV-01-CA-02"></a>

**HU-PROV-01/CA-02.** Dado que busco por nombre o RUC, cuando el sistema filtra, entonces muestra únicamente los proveedores que coinciden.

#### Casos de prueba escritos

<a id="CP-HU-PROV-01-001"></a>
##### CP-HU-PROV-01-001 · Listar y buscar proveedores homónimos

**Cubre:** HU-PROV-01/CA-01, HU-PROV-01/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN/ALMACENERO; Distribuidora Sol RUC20123456789 activa, homónima RUC20987654321 inactiva, teléfono+51 999 111 222.

1. Abrir lista; buscar Sol y RUC20123456789; limpiar.
2. Consultar se lector de recepción y varianteq NUL.

**Resultados esperados:** Nombre, RUC, estado, teléfono distinguen homónimos. Se lector solo activos y ausencia declarada; historial conserva inactivo. Búsqueda NUL alerta control a da/cero filas, no 500.

<a id="HU-PROV-02"></a>

### HU-PROV-02 · Proveedores — Registrar nuevo proveedor

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** S. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero registrar un nuevo proveedor con su nombre, RUC y teléfono, para asociarlo a las entradas de mercadería y solicitudes de compra.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 27.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-04; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-04-RUC-VALIDACION](#contrato-DEC-04-RUC-VALIDACION), [DOC-00-01](#contrato-DOC-00-01).

#### Criterios de aceptación

<a id="HU-PROV-02-CA-01"></a>

**HU-PROV-02/CA-01.** Dado que completo el formulario con nombre, RUC y datos de contacto del proveedor, cuando guardo, entonces el proveedor queda registrado con estado Activo y disponible para pedidos.

<a id="HU-PROV-02-CA-02"></a>

**HU-PROV-02/CA-02.** Dado que ingreso un RUC que ya pertenece a otro proveedor registrado, cuando intento guardar, entonces el sistema muestra «El RUC ya está registrado» y no crea el duplicado.

<a id="HU-PROV-02-CA-03"></a>

**HU-PROV-02/CA-03.** Dado que omito el RUC o el nombre, cuando intento guardar, entonces el sistema indica los campos obligatorios faltantes y no registra el proveedor.

#### Casos de prueba escritos

<a id="CP-HU-PROV-02-001"></a>
##### CP-HU-PROV-02-001 · Alta y validaciones de formato

**Cubre:** HU-PROV-02/CA-01, HU-PROV-02/CA-02, HU-PROV-02/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Abastos Norte, RUC20612345678, teléfono+51 (1) 555-1234; variantes RUC duplicado/10 dígitos/dígitos Unicode; nombre---; teléfono abc; teléfono vacío.

1. Guardar alta válida y consultar.
2. Restaurar antes de cada variante inválida; enviar formulario vacío y POST alterado.

**Resultados esperados:** Alta única activa; teléfono vacío permitido. RUC11 dígitos ASCII único, nombre con letra/número, teléfono hasta 20 con al menos un dígito; inválidos/vacíos obligatorios no guardan. RUC se rotula validación de formato, nunca certificación SUNAT.

<a id="HU-PROV-03"></a>

### HU-PROV-03 · Proveedores — Editar datos de un proveedor

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero actualizar el nombre, RUC o teléfono de un proveedor, para mantener vigentes sus datos comerciales.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-PROV-02.

**Orden de producto:** 74.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-04; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-PROV-03-CA-01"></a>

**HU-PROV-03/CA-01.** Dado que edito los datos de contacto de un proveedor, cuando guardo, entonces los cambios se reflejan de inmediato.

<a id="HU-PROV-03-CA-02"></a>

**HU-PROV-03/CA-02.** Dado que edito el RUC de un proveedor con un valor que ya pertenece a otro, cuando intento guardar, entonces el sistema advierte que el RUC ya existe y no guarda el cambio.

#### Casos de prueba escritos

<a id="CP-HU-PROV-03-001"></a>
##### CP-HU-PROV-03-001 · Editar proveedor sin reescribir recepción

**Cubre:** HU-PROV-03/CA-01, HU-PROV-03/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; proveedor Sol con recepción histórica y otro RUC ocupado.

1. Editar nombre/teléfono válidos.
2. Revisar recepción histórica.
3. Intentar RUC duplicado y nombre vacío.

**Resultados esperados:** Datos maestros válidos actualizados; snapshots históricos originales conservados. Duplicado/vacío rechaza sin cambio. Campos exactos de RUC editable se refinan al seleccionar la HU.

<a id="HU-PROV-04"></a>

### HU-PROV-04 · Proveedores — Gestionar estado de vigencia del proveedor

**Épica:** EPIC-CAT. **Prioridad MoSCoW:** S. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero cambiar el estado de un proveedor entre Activo e Inactivo, para pausar pedidos a proveedores sin relación vigente sin perder su historial.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-PROV-01.

**Orden de producto:** 29.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-04; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-04-RUC-VALIDACION](#contrato-DEC-04-RUC-VALIDACION).

#### Criterios de aceptación

<a id="HU-PROV-04-CA-01"></a>

**HU-PROV-04/CA-01.** Dado un proveedor activo, cuando ADMIN revisa y confirma su desactivación, entonces deja de estar disponible para nuevas recepciones directas; un formulario antiguo que aún lo seleccione se rechaza sin ingresar stock. La historia conserva su identidad y datos conocidos. La elegibilidad de solicitudes SOL se aplicará cuando esa función futura sea seleccionada.

<a id="HU-PROV-04-CA-02"></a>

**HU-PROV-04/CA-02.** Dado un proveedor inactivo, cuando ADMIN revisa y confirma su reactivación, entonces vuelve a estar disponible para nuevas recepciones sin alterar sus registros históricos ni otros proveedores. Las solicitudes SOL siguen futuras.

<a id="HU-PROV-04-CA-03"></a>

**HU-PROV-04/CA-03.** Dado que un proveedor está inactivo, cuando consulto la lista general, entonces se visualiza claramente como «Inactivo» conservando su historial previo.

#### Casos de prueba escritos

<a id="CP-HU-PROV-04-001"></a>
##### CP-HU-PROV-04-001 · Vigencia afecta nuevas recepciones, conserva historia

**Cubre:** HU-PROV-04/CA-01, HU-PROV-04/CA-02, HU-PROV-04/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; proveedor Sol activo con recepción previa; ALMACENERO tiene formulario antiguo seleccionándolo.

1. Desactivar mediante destino false explícito; reenviar false.
2. Enviar recepción desde formulario antiguo.
3. Reactivar confirmando y volver a seleccionar; POST sin destino.

**Resultados esperados:** Desactivar excluye de nuevas recepciones; repetición no alterna; formulario antiguo rechaza proveedor inactivo sin ingresar stock. Historia sigue visible. Reactivar permite nuevas selecciones; destino omitido rechaza. SOL futuro aplicará la misma elegibilidad sin ser requisito de recepción actual.

<a id="EPIC-INV"></a>

## EPIC-INV · Mercadería y reposición

<a id="HU-INV-01a"></a>

### HU-INV-01a · Registrar las existencias iniciales por lotes

**Épica:** EPIC-INV. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén, quiero ingresar las existencias iniciales de un producto de cualquier categoría activa, por unidad y con vencimiento obligatorio, mediante uno o varios lotes, para tener mercadería disponible para la venta con sus fechas de vencimiento controladas.

**Reglas relacionadas:** RN-01, RN-03, RN-14, RN-19, RN-29. **Dependencias funcionales:** HU-PROD-02.

**Orden de producto:** 4.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-05; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AH-01](#contrato-DOC-03AH-01), [DEC-05-LOTE-ESPACIOS](#contrato-DEC-05-LOTE-ESPACIOS), [CT-ROLLBACK-01-POST-ESCRITURA](#contrato-CT-ROLLBACK-01-POST-ESCRITURA).

#### Criterios de aceptación

<a id="HU-INV-01a-CA-01"></a>

**HU-INV-01a/CA-01.** Dado que ingreso con rol `ALMACENERO` y el producto aún no tiene una carga inicial confirmada, cuando envío uno o varios lotes válidos, entonces el sistema confirma una única carga directa sin pedido previo; cualquier otro rol recibe una denegación y no altera existencias (RN-01, RN-29).

<a id="HU-INV-01a-CA-02"></a>

**HU-INV-01a/CA-02.** Dado que completo cada lote, cuando el sistema lo valida, entonces exige número comercial no vacío normalizado y no repetido dentro de la carga, cantidad entera positiva, costo unitario positivo con máximo cuatro decimales y vencimiento posterior a hoy en America/Lima (RN-03); límites y normalización siguen el contrato DEC-05-LOTE-ESPACIOS de este documento. Las recepciones posteriores conservan identidad propia conforme a DOC-03AI-01.

<a id="HU-INV-01a-CA-03"></a>

**HU-INV-01a/CA-03.** Dado que algún lote es inválido o repetido, o que ya existe o compite simultáneamente otra carga inicial para el producto, cuando intento confirmar, entonces el sistema rechaza toda la operación y no guarda lotes, existencias ni costo; como máximo una carga concurrente puede resultar confirmada (RN-01).

<a id="HU-INV-01a-CA-04"></a>

**HU-INV-01a/CA-04.** Dado que todos los lotes son válidos, cuando se confirma la carga, entonces las existencias del producto equivalen a la suma de sus cantidades, el producto queda vendible y su costo promedio inicial se obtiene ponderando cantidad por costo, almacenado con cuatro decimales `HALF_UP` y mostrado con dos (RN-14).

<a id="HU-INV-01a-CA-05"></a>

**HU-INV-01a/CA-05.** Dado que los lotes quedaron guardados, cuando se revisan sus datos, entonces cada uno conserva su número comercial, cantidad disponible, costo, vencimiento, instante de ingreso inmutable y un identificador interno; la futura salida FEFO ordena por vencimiento, instante de ingreso e identificador interno (RN-19).

#### Casos de prueba escritos

<a id="CP-HU-INV-01a-001"></a>
##### CP-HU-INV-01a-001 · Carga inicial ponderada y trazable

**Cubre:** HU-INV-01a/CA-01, HU-INV-01a/CA-02, HU-INV-01a/CA-04, HU-INV-01a/CA-05. **Estado:** EJECUTADO PARCIAL en segunda pasada `05-M` (14/11/2026) sobre muestra aislada (`80/80` focal, `644/644` regresión Django, `126/126` Chrome multirol, `8/8` PostgreSQL `18.4`, `5/5` verificación `05-M-reval`): costo promedio ponderado exacto a `4` decimales (`S/ 2,84` visible en constancia), cabecera y líneas `InitialLoadLine` con snapshots de producto, autor, proveedor/RUC y vencimientos, y enlace en Kardex/stock; `PG 17`, lectores físicos y base operativa siguen pendientes. [Informe 05-M](auditoria_por_etapas/resultados/ETAPA-05.md#reval-05m-20261114)
**Evidencia de ejecución:** [Suite focal 05](auditoria_por_etapas/resultados/evidencias/05-tests-20261114T214206647721Z-c30fac8c/test_output.txt), [Chrome multirol 05](auditoria_por_etapas/resultados/evidencias/05-browser-20261114T213832599628Z-a1ecc756/browser.json), [PostgreSQL 18.4 05](auditoria_por_etapas/resultados/evidencias/05-postgresql-20261115T023932813038Z.json), [Verificación 05-M](auditoria_por_etapas/resultados/evidencias/05-M-reval-20261114T213817Z-f64f6a5a.json).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ALMACENERO; producto nuevo Leche sin carga, lotes A:10×2 vence 13/11/2026 y B:10×4 vence 12/12/2026; hoy 12/11Lima.

1. Abrir carga inicial.
2. Completar ambos lotes y confirmar.
3. Abrir constancia y consultar lotes/stock/costo/instantes/I Ds.

**Resultados esperados:** Una carga, dos lotes con identidad e ingreso inmutable; físico 20, vendible 20, promedio 3.0000 mostrado 3.00. Queda vendible; no cambia caja/ventas. FEFO ordena A antes de B.

<a id="CP-HU-INV-01a-002"></a>
##### CP-HU-INV-01a-002 · Rechazo íntegro y carga única concurrente

**Cubre:** HU-INV-01a/CA-01, HU-INV-01a/CA-02, HU-INV-01a/CA-03. **Estado:** EJECUTADO PARCIAL en segunda pasada `05-M` (14/11/2026): atomicidad ante fila inválida, cantidad `0/1.5/1000000`, costo `0/1.00001/10000000`, vencimiento hoy Lima (`23:30` Lima), duplicado `" ab  12 "` vs `"AB 12"`, roles `ADMIN`/`VENDEDOR` (`403`) y anónimo (`302`), bloqueo mutuo y exclusividad de carga única en `PostgreSQL 18.4` (`8/8` + `67/67` HTTP concurrente), teclado (`64/64`) y móvil `390×844` (`110/110`). Observaciones sin cierre normativo/código: divergencia `max_length=64` formulario vs servicio (`OBS-05M-01`) y `Cache-Control` vacío en `403`/`302` (`OBS-05M-02`); `PG 17` y lector de pantalla pendientes. [Informe 05-M](auditoria_por_etapas/resultados/ETAPA-05.md#reval-05m-20261114)
**Evidencia de ejecución:** [PostgreSQL 18.4 05](auditoria_por_etapas/resultados/evidencias/05-postgresql-20261115T023932813038Z.json), [Red HTTP/PG 05](auditoria_por_etapas/resultados/evidencias/05-J-network-20261115T023959234433Z.json), [Teclado Chrome 05](auditoria_por_etapas/resultados/evidencias/05-keyboard-20261114T213952534972Z-5d3a53b9/keyboard.json), [Móvil 390px Chrome 05](auditoria_por_etapas/resultados/evidencias/05-narrow-20261114T214049564964Z-106b4e77/narrow.json), [Verificación 05-M](auditoria_por_etapas/resultados/evidencias/05-M-reval-20261114T213817Z-f64f6a5a.json).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Producto sin carga; variantes: lote vacío; ab  12 junto a AB 12; cantidad 0/1.5/1000000; costo 0/1.00001; vence hoy; rol ADMIN/VENDEDOR; dos conexiones PG para mismo producto.

1. Enviar cada variante en base restaurada y comparar tablas/costo.
2. Con datos válidos sincronizar dos confirmaciones desde conexiones independientes en Postgre SQL.
3. Reintentar carga tras éxito.

**Resultados esperados:** Errores identifican campo/permiso sin carga parcial, stock ni costo nuevo. Dos cargas concurrentes dejan exactamente una carga y 20 unidades; segunda carga rechaza. La barrera debe de mostrar solapamiento, no dos llamadas secuenciales.

<a id="CP-HU-INV-01a-003"></a>
##### CP-HU-INV-01a-003 · Carga original frente a cambios posteriores

**Cubre:** HU-INV-01a/CA-01, HU-INV-01a/CA-03, HU-INV-01a/CA-04, HU-INV-01a/CA-05, HU-INV-04/CA-03. **Estado:** EJECUTADO PARCIAL (14-H1 + revalidación `05-M` 14/11/2026): snapshots de carga inicial frente a mutaciones posteriores, recepciones y ventas FEFO revalidados en Chrome (`126/126`) y `PostgreSQL 18.4` (`pg_dec_05_lot_spacing_and_initial_load_line_snapshot`); hallazgo reproducido **`DEF-05M-01`** (`r1-pmv/inventory/views.py:165`): lotes creados por ajuste positivo posterior se clasifican como legado sin fotografía original en constancia (Kardex sí identifica el ajuste). `PG 17` y base operativa pendientes. [Informe 05-M](auditoria_por_etapas/resultados/ETAPA-05.md#reval-05m-20261114)
**Evidencia de ejecución:** [14-H1 servidor](auditoria_por_etapas/resultados/evidencias/14-H-20261113/servidor/INFORME.md), [14-H1 navegador](auditoria_por_etapas/resultados/evidencias/14-H-20261113/navegador/RESUMEN.md), [PostgreSQL 18.4 05](auditoria_por_etapas/resultados/evidencias/05-postgresql-20261115T023932813038Z.json), [Verificación 05-M](auditoria_por_etapas/resultados/evidencias/05-M-reval-20261114T213817Z-f64f6a5a.json), [Chrome multirol 05](auditoria_por_etapas/resultados/evidencias/05-browser-20261114T213832599628Z-a1ecc756/browser.json).
**Precondiciones:** Base aislada; producto sin carga y tres roles ficticios; proveedor activo. DOC-03AI exige conservar cantidad y maestros originales.
**Datos de prueba:** A 1:3×2.1234 y B:7×4, ambos vigentes; promedio inicial3.4370. Cambiar nombre/código de producto, autor y proveedor; ajuste positivo2 sobreA 1; recepción posterior independiente. Legado sin fotografía.

1. Confirmar carga por ALMACENERO; verificar cabecera, líneas y promedio en la misma transacción.
2. Renombrar los maestros; consultar como ADMIN/ALMACENERO, recargar y seguir el enlace desde movimientos. Denegar VENDEDOR y altas de otros roles sin mutación.
3. Ajustar+2; comprobar cantidad original3 frente a disponible5. Registrar recepción y salidas; no mezclar sus cantidades con la carga original.
4. Inyectar un fallo después de cada escritura y comparar todas las tablas de negocio. Ensayar migración desde esquema anterior sin rellenar historia.
5. Consultar legado; separar datos actuales y cantidad original no disponible. No inferir cantidad original restando ajustes de una capacidad mutable.

**Resultados esperados:** Cabecera original y dos líneas originales conservadas; costo unitario4decimales, promedio inicial2decimales y stock/costo actual rotulados por separado. Carga única; fallos y denegaciones no mutan. Ninguna fotografía inventada para legado. ConcurrenciaPG y protección ante escrituras directas requieren etapa15; este caso no acredita saldo/filtros/paginación delKardex.

<a id="HU-INV-01b"></a>

### HU-INV-01b · Registrar recepción posterior y actualizar costo promedio

**Épica:** EPIC-INV. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 8 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como almacenero, quiero registrar recepciones posteriores directas con identidad propia y costo promedio coherente, para incorporar mercadería autorizada por el procedimiento externo del negocio, sin repetir la carga inicial ni duplicar existencias al reenviar.

**Reglas relacionadas:** RN-01, RN-03, RN-14, RN-19, RN-29. **Dependencias funcionales:** HU-INV-01a.

**Orden de producto:** 30.

**Estimación:** Identidad propia, correlativo, idempotencia, trazabilidad y concurrencia de recepción.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AB-01](#contrato-DOC-03AB-01), [DOC-03AH-01](#contrato-DOC-03AH-01), [DOC-03AI-01](#contrato-DOC-03AI-01), [DEC-05-LOTE-ESPACIOS](#contrato-DEC-05-LOTE-ESPACIOS), [DEC-04-RUC-VALIDACION](#contrato-DEC-04-RUC-VALIDACION), [DEC-08-KARDEX-COMPRAS](#contrato-DEC-08-KARDEX-COMPRAS), [CT-ROLLBACK-01-POST-ESCRITURA](#contrato-CT-ROLLBACK-01-POST-ESCRITURA).

#### Criterios de aceptación

<a id="HU-INV-01b-CA-01"></a>

**HU-INV-01b/CA-01.** Dado que un producto ya completó su carga inicial, tenga o no existencias remanentes, cuando ALMACENERO confirma una recepción posterior directa, con identidad propia, cantidad y costo de compra, entonces el sistema recalcula el costo promedio usando todas las unidades físicas registradas anteriores, incluidas las vencidas pendientes de baja, y las ingresadas conforme a RN-14; el reintento de la misma clave/contenido devuelve la recepción previa sin nuevos efectos.

<a id="HU-INV-01b-CA-02"></a>

**HU-INV-01b/CA-02.** Dado que consulto el costo promedio después de la entrada, cuando lo comparo con el cálculo ponderado, entonces coincide con el valor almacenado a cuatro decimales y se muestra redondeado a dos, sin alterar costos históricos de ventas anteriores.

#### Casos de prueba escritos

<a id="CP-HU-INV-01b-001"></a>
##### CP-HU-INV-01b-001 · Recepción, promedio físico e identidad propia

**Cubre:** HU-INV-01b/CA-01, HU-INV-01b/CA-02. **Estado:** EJECUTADO PARCIAL en revalidación puntual ETAPA-06 (14/11/2026): se conserva 14-G y se ejecuta la variante exacta F-COSTO (`18@3` con 8 vencidas + `10@6` → `R-00000001`, físico 28, vendible 20, promedio `4.0714` mostrado `S/ 4,07`), segunda recepción `C@8` (`33@4.6666`), reintento idéntico/divergente y concurrencia aislada PG `18.4`. Pendientes: `PG 17` objetivo, caída real `SIGKILL`, datos operativos y ajuste visual móvil `390×844` en constancia. [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114) · [Evidencia 14-G](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g).
**Evidencia de ejecución:** [ETAPA-06 servidor](auditoria_por_etapas/resultados/evidencias/06-reval-server-20261114T212733200909Z-caa926fa/report.json), [ETAPA-06 Chrome](auditoria_por_etapas/resultados/evidencias/06-reval-browser-20261114T212745468050Z-dce3e1b1/browser.json), [ETAPA-06 PG 18.4](auditoria_por_etapas/resultados/evidencias/06-reval-pg18-20261114T213329260785Z.json), [14-G servidor](auditoria_por_etapas/resultados/evidencias/14-G-20261113/servidor/INFORME.md), [14-G navegador](auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/RESUMEN.md).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ALMACENERO; variante F-COSTO: físico 18 promedio 3,8 vencidas/10 vigentes; recibe 10×6 lote C vigente; clave11111111-1111-4111-8111-111111111111; proveedor opcional.

1. Confirmar recepción directa sin SOL.
2. Leer referencia/autor/costo/stock.
3. Reenviar misma clave y contenido; cambiar cantidad a 11 con la misma clave.
4. Crear otro ingreso real del mismo lote C con clave nueva y fecha coherente.

**Resultados esperados:** Primera: referencia propia R-00000001 si contador inicial 0; físico 28, vendible 20, promedio 4.0714 mostrado 4.07. Reintento devuelve misma recepción sin mutar; contenido divergente rechaza. Segunda recepción real conserva origen separado y recalcula promedio con su entrada; no retorna referencia de la carga inicial ni altera venta histórica de costo 3.

<a id="HU-INV-02"></a>

### HU-INV-02 · Inventario — Registrar baja de inventario por merma

**Épica:** EPIC-INV. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén, quiero registrar la baja de productos deteriorados, vencidos o sustraídos indicando su lote y causa reconocida, para retirar mercadería no vendible y justificar la pérdida.

**Reglas relacionadas:** RN-04, RN-05, RN-14, RN-20, RN-29. **Dependencias funcionales:** HU-INV-01a.

**Orden de producto:** 24.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-08; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AH-01](#contrato-DOC-03AH-01), [DEC-05-LOTE-ESPACIOS](#contrato-DEC-05-LOTE-ESPACIOS), [RN-05](#contrato-RN-05).

#### Criterios de aceptación

<a id="HU-INV-02-CA-01"></a>

**HU-INV-02/CA-01.** Dado que selecciono un lote de producto, cuando indico la cantidad a retirar y la causa (Vencimiento, Daño o rotura, o Robo o faltante), entonces el sistema descuenta las unidades validando que no superen las existencias del lote (RN-04, RN-05).

<a id="HU-INV-02-CA-02"></a>

**HU-INV-02/CA-02.** Dado que el lote ya alcanzó su fecha de vencimiento según la hora de Lima, cuando se intenta registrar una baja, entonces permite Vencimiento si la causa es caducidad o Robo o faltante con explicación si esa es la causa real, y rechaza Daño o rotura conforme a RN-05.

<a id="HU-INV-02-CA-03"></a>

**HU-INV-02/CA-03.** Dado que la causa seleccionada es Daño o rotura o Robo o faltante, cuando se registra la baja, entonces el sistema exige obligatoriamente detallar lo ocurrido e identifica al empleado responsable (RN-20).

<a id="HU-INV-02-CA-04"></a>

**HU-INV-02/CA-04.** Dado que se confirma la baja, cuando termina la operación, entonces el sistema genera una constancia interna de merma con número correlativo, producto, lote, fecha y motivo.

#### Casos de prueba escritos

<a id="CP-HU-INV-02-001"></a>
##### CP-HU-INV-02-001 · Causas de merma y constancia

**Cubre:** HU-INV-02/CA-01, HU-INV-02/CA-02, HU-INV-02/CA-03, HU-INV-02/CA-04. **Estado:** EJECUTADO en muestras14-I revalidadas en14-CIERRE: causas, constancia, fotografías, roles, costo y legado. Impresiónweb observada; dispositivo físico y escrituraSQL privilegiada no verificados.
**Evidencia de ejecución:** Corte vigente14-CIERRE. [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt), [PostgreSQL](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.
**Evidencia de ejecución:** [Servidor14-I](auditoria_por_etapas/resultados/evidencias/14-I-20261114/servidor/INFORME.md), [Chrome14-I](auditoria_por_etapas/resultados/evidencias/14-I-20261114/navegador/RESUMEN.md).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Variantes independientes: lote E vencido con 3 unidades; lote A vigente 10; roles ADMIN/ALMACENERO; cantidad 1; motivos VENCIMIENTO, DAÑO, ROBO; explicación Frasco roto / faltante confirmado por conteo.

1. Registrar vencimiento de E.
2. Restaurar: intentar daño de E y vencimiento de A.
3. Restaurar: registrar robo de E con y sin explicación; daño de A con explicación.
4. Abrir constancia e inspeccionar saldo, autor, costo y caja.

**Resultados esperados:** Vencimiento de E, robo explicado de E y daño explicado de A se aceptan en tres variantes independientes, cada una con una salida y constancia correlativa inmutable. Daño de E, vencimiento de A y robo/daño sin explicación rechazan sin mutación. Caja/ventas/precio intactos; promedio conservado si queda físico. VENDEDOR denegado.

<a id="CP-HU-INV-02-002"></a>
##### CP-HU-INV-02-002 · Exceso y repetición de baja

**Cubre:** HU-INV-02/CA-01, HU-INV-02/CA-04. **Estado:** EJECUTADO en muestras14-CIERRE: exceso y claves inválidas/divergentes rechazan; mismaUUID recupera un resultado entre sesiones y en PostgreSQL concurrente. Sin nueva baja ni descuento duplicado.
**Evidencia de ejecución:** Corte vigente14-CIERRE. [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt), [PostgreSQL](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.
**Evidencia de ejecución:** [Servidor14-I](auditoria_por_etapas/resultados/evidencias/14-I-20261114/servidor/INFORME.md), [Chrome14-I](auditoria_por_etapas/resultados/evidencias/14-I-20261114/navegador/RESUMEN.md).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Lote A10; baja 11 y luego baja 2 válida con misma clave de operación en dos conexiones PG.

1. Enviar 11.
2. Sin cambiar fixture, sincronizar dos envíos idénticos de 2.
3. Consultar saldo, movimientos y constancia.

**Resultados esperados:** 11 rechaza sin cambio. Doble envío lógico crea una baja de 2, saldo 8 y una constancia; jamás saldo negativo. Capturar evidencia del solapamiento y de todas las tablas afectadas.

<a id="HU-INV-03"></a>

### HU-INV-03 · Inventario – Realizar ajuste por conteo físico

**Épica:** EPIC-INV. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 8 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero registrar ajustes positivos o negativos de productos con carga inicial confirmada tras contar físicamente los estantes, para cuadrar las diferencias entre lo contado y el sistema manteniendo el control por lote.

**Reglas relacionadas:** RN-01, RN-03, RN-14, RN-29. **Dependencias funcionales:** HU-INV-01a.

**Orden de producto:** 25.

**Estimación:** Nuevos lotes por ajuste, valoración, legado y carreras de inventario.

**Procedencia:** ETAPA-08; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AH-01](#contrato-DOC-03AH-01), [DEC-05-LOTE-ESPACIOS](#contrato-DEC-05-LOTE-ESPACIOS), [RN-05](#contrato-RN-05).

#### Criterios de aceptación

<a id="HU-INV-03-CA-01"></a>

**HU-INV-03/CA-01.** Dado que el conteo en mostrador revela unidades de más (ajuste positivo), cuando el administrador lo registra, entonces exige asociarlo a un lote o crear uno nuevo con fecha de vencimiento fiable, motivo y costo conforme a RN-14; un hallazgo vencido se registra solo como no vendible, nunca como recepción ordinaria.

<a id="HU-INV-03-CA-02"></a>

**HU-INV-03/CA-02.** Dado que el conteo revela unidades de menos (ajuste negativo), cuando el administrador lo registra, entonces el sistema exige indicar de qué lote específico se descuentan las unidades.

<a id="HU-INV-03-CA-03"></a>

**HU-INV-03/CA-03.** Dado que se confirma el ajuste físico, cuando el sistema lo guarda, entonces genera un registro con fecha, cantidad ajustada, empleado responsable y motivo obligatorio.

#### Casos de prueba escritos

**Concreción14-CIERRE, aceptada14/11/2026.** La orden expresa del responsable de corregir los pendientes hasta completar14 respalda esta realización técnica de HU-INV-03, RN05 y RN14: se reutiliza PhysicalAdjustment con fotografía de producto/código/unidad, responsable, lote/vencimiento/origen y costo/fuente; UUID persistente única y huella de contenido para recuperar la misma operación del mismo actor entre sesiones. HTTP exige clave; llamadas internas sin clave representan operaciones nuevas. Un lote nuevo referencia su ajuste de origen; no se inventa compra, recepción ni segunda carga inicial. Se rechaza duplicar el número comercial normalizado de un lote existente: el conteo debe seleccionar su origen ya registrado. La política de recepciones sucesivas del mismo lote comercial no cambia.

ADMIN registra y ADMIN/ALMACENERO consultan `/inventario/ajustes/{UUID}/`, enlazado desde movimientos. Legado sin fotografía muestra ausencia explícita, sin completar nombres desde maestros actuales. Con Q0 se exige costo positivo hasta9999999.9999 a4decimales y referencia documental de1..300 caracteres; con Q>0 se usa el promedio vigente y se rechaza un costo distinto. Motivo1..300, número de lote1..64, variación entera no nula de−999999..999999, nuevo lote positiva, fecha fiable hasta20años; vencido permanece físico no vendible. Producto sin carga inicial exige investigar apertura, no inventarla. La referencia es declarada por el operador, no certifica autenticidad legal.

Se acepta el resumen de errores enfocable, con enlaces a campos y mensajes inline, como concreción de CT-COHERENCIA-UI/C03 para este formulario. Se conserva la interfaz existente. La migración deja NULL en historia ausente y el efecto lote/ajuste/costo/origen es atómico. [Alternativas, beneficio, riesgo, costo e impacto](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md). Aceptación e implementación no equivalen a prueba aprobada: consultar resultados de14-CIERRE.

<a id="CP-HU-INV-03-001"></a>
##### CP-HU-INV-03-001 · Ajustes positivos y negativos documentados

**Cubre:** HU-INV-03/CA-01, HU-INV-03/CA-02, HU-INV-03/CA-03. **Estado:** EJECUTADO en primera pasada14-CIERRE,14/11/2026: ajustes existentes/nuevos, costoQ0, historia, roles, reenvío y efectos entre módulos verificados en bases aisladas. No acredita datos operativos ni defensa anteSQL privilegiado.
**Evidencia de ejecución:** Corte vigente14-CIERRE. [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt), [PostgreSQL](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; Leche 20 promedio 3; +2 lote A; -3 lote B; nuevo lote D con vence 15/12/2026; motivo Recuento físico documentado; variantes Q0 con/sin costo 2.5000.

1. Registrar +2 y después -3 en lotes indica dos.
2. Revisar movimientos, cantidades de origen y promedio.
3. Restaurar: crear lote D por ajuste positivo.
4. Probar Q0 sin costo, sin motivo, cantidad negativa superior al lote y actor ALMACENERO.

**Resultados esperados:** Secuencia físico 22→19 y promedio 3 conservado; ingreso original del lote no se reescribe. Nuevo D tiene origen AJUSTE, fecha/autor/motivo; si vencido es físico no vendible. Q0 exige costo positivo acreditado; faltante/permiso/exceso rechaza íntegro. No simula compra ni consume carga inicial.

<a id="HU-INV-04"></a>

### HU-INV-04 · Mercadería — Consultar movimientos de un producto

**Épica:** EPIC-INV. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 8 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o encargado del almacén, quiero consultar el historial cronológico de movimientos de un producto, para revisar las entradas, ventas, mermas y ajustes.

**Reglas relacionadas:** RN-01, RN-14, RN-25, RN-28, RN-29. **Dependencias funcionales:** HU-INV-01a, HU-VEN-01c, HU-INV-02 y HU-INV-03.

**Orden de producto:** 26.

**Estimación:** Kardex con saldo real, asignaciones de lote, filtros y paginación.

**Procedencia:** ETAPA-08; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AI-01](#contrato-DOC-03AI-01), [DEC-11-MODELO-AUDITORIA-VENTAS](#contrato-DEC-11-MODELO-AUDITORIA-VENTAS), [DEC-08-KARDEX-COMPRAS](#contrato-DEC-08-KARDEX-COMPRAS).

#### Criterios de aceptación

<a id="HU-INV-04-CA-01"></a>

**HU-INV-04/CA-01.** Dado que selecciono un producto, cuando consulto sus movimientos, entonces el sistema muestra en orden cronológico todas las entradas, salidas y saldo resultante con fecha, tipo de operación, cantidad y lote.

<a id="HU-INV-04-CA-02"></a>

**HU-INV-04/CA-02.** Dado que un movimiento nació de una recepción directa, cuando abro el detalle, entonces muestra su referencia propia, responsable y proveedor o ausencia declarada; si en el futuro nació de HU-SOL-05a, mostrará además la solicitud aprobada sin inventar esa relación para entradas actuales.

<a id="HU-INV-04-CA-03"></a>

**HU-INV-04/CA-03.** Dado que una entrada provino de carga inicial o ajuste, cuando abro el detalle, entonces se etiqueta como carga directa o ajuste con su motivo y responsable.

<a id="HU-INV-04-CA-04"></a>

**HU-INV-04/CA-04.** Dado que aplico filtros por fechas o tipo de movimiento, cuando ejecuto la búsqueda, entonces se visualizan solo las operaciones coincidentes.

#### Casos de prueba escritos

<a id="CP-HU-INV-04-001"></a>
##### CP-HU-INV-04-001 · Kardex con saldo real y filtros

**Cubre:** HU-INV-04/CA-01, HU-INV-04/CA-02, HU-INV-04/CA-03, HU-INV-04/CA-04. **Estado:** EJECUTADO PARCIAL14-H2. Secuencia, filtros, saldo conocido, paginación y permisos en SQLite/Chrome; autor histórico de ajustes y garantías concurrentes conservan pendientes.
**Evidencia de ejecución:** [Servidor14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/servidor/INFORME.md), [Navegador14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/navegador/RESUMEN.md).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN/ALMACENERO; secuencia conocida: carga 20, recepción 10 ref R-00000001, venta 5, merma 2, ajuste+1; instantes ordenados 12/11 09:00..13:00 Lima.

1. Abrir movimientos.
2. Ver detalles de carga, recepción y ajuste.
3. Filtrar 10:00..13:00 y solo SALIDA.
4. Paginar fixture de 26 movimientos con mismo instante y I Ds distintos.

**Resultados esperados:** Saldos 20,30,25,23,24; origen/autor/lote/ref conservados. Filtro SALIDA muestra 5 y 2 sin fingir saldo-7: apertura real y saldo por movimiento consideran entradas omitidas. Orden instante+ID ascendente,25/página y filtros persistidos; legado sin lote figura desconocido. GET no muta; VENDEDOR no accede a costos.

<a id="HU-INV-05"></a>

### HU-INV-05 · Inventario — Consultar historial de bajas

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero consultar el historial de todas las bajas de mercadería registradas, para vigilar las pérdidas y analizar sus causas.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-INV-02.

**Orden de producto:** 34.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-08; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-INV-05-CA-01"></a>

**HU-INV-05/CA-01.** Dado que accedo al historial de bajas, cuando la lista carga, entonces veo por cada baja: producto, motivo, número de lote, cantidad, empleado que la registró y fecha.

<a id="HU-INV-05-CA-02"></a>

**HU-INV-05/CA-02.** Dado que filtro por motivo o período de tiempo, cuando aplico el filtro, entonces el sistema muestra únicamente las bajas coincidentes.

#### Casos de prueba escritos

<a id="CP-HU-INV-05-001"></a>
##### CP-HU-INV-05-001 · Historial futuro de bajas

**Cubre:** HU-INV-05/CA-01, HU-INV-05/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; bajas 12/11: E vencimiento 2 y A daño 1 por almacén; 11/11 robo 3.

1. Como ADMIN/ALMACENERO abrir historial.
2. Filtrar 12/11 y motivo DAÑO.
3. Elegir rango sin datos.

**Resultados esperados:** Lista incluye producto/lote/unidades/motivo/empleado/fecha. Filtro devuelve solo A1; rango vacío informa sin registros. No modifica stock ni expone permisos adicionales.

<a id="HU-INV-06"></a>

### HU-INV-06 · Inventario — Consultar historial de ajustes

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero consultar el historial de ajustes por conteo físico, para verificar las correcciones realizadas en las existencias.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-INV-03.

**Orden de producto:** 35.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-08; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-INV-06-CA-01"></a>

**HU-INV-06/CA-01.** Dado que accedo al historial de ajustes, cuando la lista carga, entonces veo por cada ajuste: producto, tipo (positivo o negativo), cantidad ajustada, responsable y fecha.

<a id="HU-INV-06-CA-02"></a>

**HU-INV-06/CA-02.** Dado que filtro por producto o rango de fechas, cuando aplico el filtro, entonces el sistema exhibe los registros correspondientes.

#### Casos de prueba escritos

<a id="CP-HU-INV-06-001"></a>
##### CP-HU-INV-06-001 · Historial futuro de ajustes

**Cubre:** HU-INV-06/CA-01, HU-INV-06/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; Leche+2 y Arroz-1 el 12/11; Leche-3 el 11/11.

1. Abrir historial; filtrar Leche y 12/11.
2. Limpiar filtros y consultar detalle.

**Resultados esperados:** Filtro muestra solo Leche+2; lista completa mantiene signos, producto, cantidad, responsable, fecha y motivo enlazado. Consulta no cambia saldos.

<a id="HU-SOL-01"></a>

### HU-SOL-01 · Reposición – Crear solicitud de reposición

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén, quiero generar una solicitud de reposición seleccionando productos y un proveedor habitual, para pedir la compra de mercadería al administrador.

**Reglas relacionadas:** RN-06. **Dependencias funcionales:** HU-PROD-02, HU-PROV-02.

**Orden de producto:** 46.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-SOL-01-CA-01"></a>

**HU-SOL-01/CA-01.** Dado que elaboro una nueva solicitud, cuando elijo un proveedor activo y agrego productos indicando las cantidades requeridas, entonces el sistema crea la solicitud en estado Pendiente.

<a id="HU-SOL-01-CA-02"></a>

**HU-SOL-01/CA-02.** Dado que agrego artículos con existencias iguales o inferiores a su mínimo configurado —10 solo cuando se conservó el valor predeterminado—, cuando el sistema carga la sugerencia, entonces propone dichos artículos para facilitar el pedido (RN-06).

<a id="HU-SOL-01-CA-03"></a>

**HU-SOL-01/CA-03.** Dado que intento registrar una solicitud sin productos o con cantidades menores o iguales a cero, cuando intento guardarla, entonces el sistema bloquea el envío y exige ingresar productos válidos.

#### Casos de prueba escritos

<a id="CP-HU-SOL-01-001"></a>
##### CP-HU-SOL-01-001 · Solicitud futura y sugerencia de mínimo

**Cubre:** HU-SOL-01/CA-01, HU-SOL-01/CA-02, HU-SOL-01/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ALMACENERO; proveedor Sol activo; Arroz 5 mínimo 10; Leche 20 mínimo 10; pedir Arroz 12; variantes sin líneas/0/-1/proveedor inactivo.

1. Crear solicitud y revisar sugeridos.
2. Confirmar Arroz 12.
3. Restaurar antes de cada variante inválida y enviar.

**Resultados esperados:** Sugiere Arroz por 5<=10; no Leche. Solicitud Pendiente con 12 y proveedor Sol; stock/costo/caja no cambian. Inválidos rechazan íntegro; no se conf un de pedido con recepción.

<a id="HU-SOL-02"></a>

### HU-SOL-02 · Reposición — Listar solicitudes con filtro por estado

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén o administrador, quiero consultar la lista de solicitudes de reposición filtrando por estado, para hacer seguimiento a los pedidos.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-SOL-01.

**Orden de producto:** 47.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-SOL-02-CA-01"></a>

**HU-SOL-02/CA-01.** Dado que ingreso a la sección de solicitudes, cuando filtro por estado (Pendiente, Aprobada, Rechazada, Parcialmente atendida o Completada), entonces el sistema muestra con exactitud las solicitudes coincidentes.

<a id="HU-SOL-02-CA-02"></a>

**HU-SOL-02/CA-02.** Dado que elijo una solicitud, cuando abro su detalle, entonces veo productos pedidos, cantidades, fecha, proveedor y observaciones.

<a id="HU-SOL-02-CA-03"></a>

**HU-SOL-02/CA-03.** Dado que no existen solicitudes con el estado elegido, cuando filtro, entonces la pantalla informa que no hay registros.

#### Casos de prueba escritos

<a id="CP-HU-SOL-02-001"></a>
##### CP-HU-SOL-02-001 · Estados, detalle y ausencia de pedidos

**Cubre:** HU-SOL-02/CA-01, HU-SOL-02/CA-02, HU-SOL-02/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; solicitudes S1Pendiente, S2Aprobada, S3Rechazada, S4Parcialmente atendida, S5Completada; S2Arroz 12/Sol.

1. Filtrar cada estado.
2. Abrir S2.
3. Repetir con fixture sin solicitudes.

**Resultados esperados:** Cada filtro devuelve solo estado correspondiente; detalle S2 muestra producto 12, proveedor, fecha y observación; ausencia informa sin registros. Sin cambios de estado/stock.

<a id="HU-SOL-03"></a>

### HU-SOL-03 · Reposición — Aprobar solicitud de reposición

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero aprobar una solicitud de reposición pudiendo cambiar el proveedor sugerido, para autorizar la compra con las mejores condiciones comerciales.

**Reglas relacionadas:** RN-16. **Dependencias funcionales:** HU-SOL-01.

**Orden de producto:** 48.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-SOL-03-CA-01"></a>

**HU-SOL-03/CA-01.** Dado que reviso una solicitud en estado Pendiente, cuando la apruebo manteniendo el proveedor sugerido, entonces la solicitud pasa a estado Aprobada con dicho proveedor (RN-16).

<a id="HU-SOL-03-CA-02"></a>

**HU-SOL-03/CA-02.** Dado que reviso una solicitud en estado Pendiente, cuando selecciono un proveedor alternativo antes de aprobar, entonces la solicitud pasa a estado Aprobada con el proveedor actualizado.

<a id="HU-SOL-03-CA-03"></a>

**HU-SOL-03/CA-03.** Dado que la solicitud queda aprobada, cuando el encargado del almacén la consulta, entonces visualiza su nuevo estado y el proveedor confirmado.

#### Casos de prueba escritos

<a id="CP-HU-SOL-03-001"></a>
##### CP-HU-SOL-03-001 · Aprobación futura con proveedor confirmado

**Cubre:** HU-SOL-03/CA-01, HU-SOL-03/CA-02, HU-SOL-03/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; S1Pendiente proveedor Sol; alternativo Norte activo; ALMACENERO consulta.

1. Aprobar S1 conservando Sol.
2. Restaurar y aprobar cambiando a Norte.
3. Consultar como ALMACENERO; reenviar aprobación obsoleta.

**Resultados esperados:** Aprobada con proveedor elegido y visible para almacén; no ingresa stock. Reenvío no duplica transición ni revierte proveedor; rol no ADMIN denegado.

<a id="HU-SOL-04"></a>

### HU-SOL-04 · Reposición — Rechazar solicitud de reposición

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero rechazar una solicitud de reposición indicando el motivo, para comunicar al almacenero la decisión tomada.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-SOL-01.

**Orden de producto:** 49.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-SOL-04-CA-01"></a>

**HU-SOL-04/CA-01.** Dado que reviso una solicitud Pendiente, cuando intento rechazarla sin escribir un motivo, entonces el sistema muestra «El motivo del rechazo es obligatorio» y no cambia el estado.

<a id="HU-SOL-04-CA-02"></a>

**HU-SOL-04/CA-02.** Dado que ingreso el motivo y confirmo, cuando el sistema lo procesa, entonces la solicitud pasa a Rechazada y el motivo queda visible para el personal.

#### Casos de prueba escritos

<a id="CP-HU-SOL-04-001"></a>
##### CP-HU-SOL-04-001 · Rechazo futuro motivado

**Cubre:** HU-SOL-04/CA-01, HU-SOL-04/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; S1Pendiente; motivo vacío y Compra no necesaria por sobre stock.

1. Intentar rechazar sin motivo.
2. Introducir motivo válido y confirmar.
3. Consultar como solicitante.

**Resultados esperados:** Primero mensaje El motivo del rechazo es obligatorio y estado Pendiente intacto; después Rechazada con motivo visible sin movimientos de stock/dinero.

<a id="HU-SOL-05a"></a>

### HU-SOL-05a · Reposición — Completar la recepción total de una solicitud

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén, quiero registrar la llegada completa de mercadería de una solicitud aprobada con lote, vencimiento y costo, para ingresar las existencias y actualizar el costo promedio.

**Reglas relacionadas:** RN-01, RN-03, RN-14, RN-19. **Dependencias funcionales:** HU-SOL-03, HU-INV-01a, HU-INV-01b.

**Orden de producto:** 50.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-SOL-05a-CA-01"></a>

**HU-SOL-05a/CA-01.** Dado que recibo todos los artículos de una solicitud aprobada, cuando registro el lote, fecha de vencimiento y costo de compra de cada uno, entonces las existencias aumentan, entran a la rotación vendiendo primero lo que vence antes (RN-19) y la solicitud pasa a Completada.

<a id="HU-SOL-05a-CA-02"></a>

**HU-SOL-05a/CA-02.** Dado que intento ingresar para un producto una cantidad mayor a la aprobada, cuando confirmo, entonces el sistema advierte el exceso y bloquea la operación.

<a id="HU-SOL-05a-CA-03"></a>

**HU-SOL-05a/CA-03.** Dado que ingreso un lote cuya fecha de vencimiento ya se cumplió o vence hoy, cuando intento confirmar, entonces el sistema bloquea la recepción conforme a la regla RN-03.

<a id="HU-SOL-05a-CA-04"></a>

**HU-SOL-05a/CA-04.** Dado que registro el costo de compra en la recepción, cuando se confirma la entrada, entonces el sistema recalcula automáticamente el costo promedio ponderado de cada producto (RN-14).

#### Casos de prueba escritos

<a id="CP-HU-SOL-05a-001"></a>
##### CP-HU-SOL-05a-001 · Recepción total futura y exc esos

**Cubre:** HU-SOL-05a/CA-01, HU-SOL-05a/CA-02, HU-SOL-05a/CA-03, HU-SOL-05a/CA-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; S1Aprobada Arroz 12; stock previo5@2; loteN12@3 vence 12/12; variantes 13 unidades/vence hoy.

1. Como ALMACENERO recibir 12.
2. Abrir solicitud/stock/costo.
3. Restaurar y probar 13 o fecha 12/11.

**Resultados esperados:** Válido: Completada, saldo 0, físico 17, promedio 2.7059, entrada trazable y lote elegible FEFO. Exceso/vencido rechazan sin recepción/estado/costo parcial; no superar saldo aprobado.

<a id="HU-SOL-05b"></a>

### HU-SOL-05b · Reposición — Registrar una recepción parcial con saldo pendiente

**Épica:** EPIC-INV. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén, quiero registrar una recepción parcial de mercadería dejando el saldo pendiente, para ingresar lo recibido y controlar lo que falta por entregar.

**Reglas relacionadas:** RN-01, RN-03, RN-14, RN-19. **Dependencias funcionales:** HU-SOL-05a.

**Orden de producto:** 51.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-06; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-SOL-05b-CA-01"></a>

**HU-SOL-05b/CA-01.** Dado que recibo solo una parte de los artículos aprobados, cuando registro las unidades recibidas con lote, vencimiento vigente posterior a hoy (RN-03) y costo de compra, entonces las existencias aumentan, el costo promedio se actualiza (RN-14) y la solicitud pasa a «Parcialmente atendida».

<a id="HU-SOL-05b-CA-02"></a>

**HU-SOL-05b/CA-02.** Dado que una solicitud está parcialmente atendida, cuando abro su detalle, entonces visualizo claramente las cantidades recibidas y el saldo pendiente de cada artículo.

<a id="HU-SOL-05b-CA-03"></a>

**HU-SOL-05b/CA-03.** Dado que llega el saldo restante de mercadería, cuando registro la segunda entrega cumpliendo fechas vigentes, entonces el sistema suma las existencias restantes con rotación de vencimiento (RN-19), pasa la solicitud a Completada y deja el saldo pendiente en cero.

#### Casos de prueba escritos

<a id="CP-HU-SOL-05b-001"></a>
##### CP-HU-SOL-05b-001 · Dos entregas futuras sin perder saldo

**Cubre:** HU-SOL-05b/CA-01, HU-SOL-05b/CA-02, HU-SOL-05b/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; S1 aprobada Arroz 12; previo5@2; primera7@3 ysegunda5@3 con lotes vigentes.

1. Recibir 7 y abrir detalle.
2. Recibir 5 restantes con otra clave.
3. Reenviar segunda entrega y probar una unidad extra.

**Resultados esperados:** Primera Parcialmente atendida, recibido 7, pendiente 5, físico 12, promedio 2.5833; segunda Completada, recibido 12, pendiente 0, físico 17, promedio 2.7059 por redondeo 4. Reintento no duplica; exceso rechaza.

<a id="EPIC-VEN"></a>

## EPIC-VEN · Ventas y caja

<a id="HU-CAJA-01"></a>

### HU-CAJA-01 · Abrir el turno de caja

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero abrir el turno de caja declarando el dinero en efectivo que tengo al comenzar, para disponer de sencillo para dar vuelto y habilitar las ventas en el mostrador.

**Reglas relacionadas:** RN-10, RN-29. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 5.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-09; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-11-TOPE-EFECTIVO-FORM](#contrato-DEC-11-TOPE-EFECTIVO-FORM).

#### Criterios de aceptación

<a id="HU-CAJA-01-CA-01"></a>

**HU-CAJA-01/CA-01.** Dado que ingreso con rol `VENDEDOR` y no existe un turno abierto, cuando declaro un monto inicial válido en soles, igual o mayor que cero y con máximo dos decimales, entonces el sistema abre un turno ligado a mi usuario y habilita la preparación de ventas (RN-10, RN-29).

<a id="HU-CAJA-01-CA-02"></a>

**HU-CAJA-01/CA-02.** Dado que ingreso un monto negativo, no numérico o con más de dos decimales, cuando intento confirmar, entonces el sistema explica la validación, no abre el turno y no registra movimiento de efectivo.

<a id="HU-CAJA-01-CA-03"></a>

**HU-CAJA-01/CA-03.** Dado que ya existe un turno abierto o dos vendedores intentan abrirlo simultáneamente, cuando el sistema procesa las solicitudes, entonces exactamente una apertura como máximo queda confirmada y las demás se rechazan sin crear turnos paralelos (RN-10).

<a id="HU-CAJA-01-CA-04"></a>

**HU-CAJA-01/CA-04.** Dado que la apertura se confirmó, cuando consulto el turno, entonces conserva vendedor responsable, caja única, dinero inicial e instante inequívoco mostrado con fecha y hora de Lima; un rol no autorizado no puede abrirlo por acceso directo (RN-29).

#### Casos de prueba escritos

<a id="CP-HU-CAJA-01-001"></a>
##### CP-HU-CAJA-01-001 · Apertura válida y límites

**Cubre:** HU-CAJA-01/CA-01, HU-CAJA-01/CA-02, HU-CAJA-01/CA-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** VENDEDORA; CAJA-01 sin turno; apertura 100.00; variantes 0, -1,1.001, abc,10000000.00; ADMIN.

1. Abrir con 100 y revisar responsable/fecha Lima.
2. Restaurar cada variante y enviar formulario y POST directo.

**Resultados esperados:** 100 abre un turno y habilita POS; 0 permitido; negativos/formato/precisión/máximo excedido rechazan sin turno/movimiento. ADMIN denegado. Instante inequívoco, caja única y dueño A.

<a id="CP-HU-CAJA-01-002"></a>
##### CP-HU-CAJA-01-002 · Dos vendedores compiten por caja única

**Cubre:** HU-CAJA-01/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Sin turno; A abre 100 y Babre 50 en dos conexiones PG independientes.

1. Colocar barrera antes de decisión de apertura y ejecutar simultáneamente.
2. Leer turnos y repetir solicitud perdedora.

**Resultados esperados:** Como máximo un abierto global; ganador conserva dueño y monto. Perdedor recibe ocupado sin turno ni movimiento adicional. No basta SQ Lite ni ejecución secuencial.

<a id="HU-CAJA-02"></a>

### HU-CAJA-02 · Cerrar y cuadrar la caja

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero cerrar mi turno de caja ingresando el dinero en efectivo contado, para generar el resumen de cuadre y comparar la plata contada contra el dinero esperado.

**Reglas relacionadas:** RN-10, RN-29, RN-30. **Dependencias funcionales:** Habilitación: HU-CAJA-01; integración del recorrido: HU-VEN-01c.

**Orden de producto:** 9.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-09; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-11-TOPE-EFECTIVO-FORM](#contrato-DEC-11-TOPE-EFECTIVO-FORM), [CT-ROLLBACK-01-POST-ESCRITURA](#contrato-CT-ROLLBACK-01-POST-ESCRITURA).

#### Criterios de aceptación

<a id="HU-CAJA-02-CA-01"></a>

**HU-CAJA-02/CA-01.** Dado que ingreso como el `VENDEDOR` responsable del turno, cuando declaro el efectivo contado, entonces el sistema exige un valor numérico igual o mayor que cero con máximo dos decimales; ante un valor inválido o un rol distinto no cierra ni modifica el turno (RN-10, RN-29).

<a id="HU-CAJA-02-CA-02"></a>

**HU-CAJA-02/CA-02.** Dado que el monto contado es válido, cuando se prepara el resumen, entonces calcula `esperado = inicial + ingresos confirmados de efectivo - salidas confirmadas de efectivo` y `diferencia = contado - esperado`, mostrando cuadre exacto, sobrante o faltante; en el alcance vigente los ingresos posteriores a la apertura son los totales de ventas en efectivo confirmadas (RN-10).

<a id="HU-CAJA-02-CA-03"></a>

**HU-CAJA-02/CA-03.** Dado que confirmo un cierre válido, cuando se guarda, entonces registra vendedor, caja, importes e instante de cierre mostrado en Lima y deja el turno cerrado de forma irreversible; un segundo intento de cierre se rechaza sin alterar el acta original (RN-10).

<a id="HU-CAJA-02-CA-04"></a>

**HU-CAJA-02/CA-04.** Dado que existe una venta en preparación con al menos una línea, cuando intento cerrar, entonces el sistema bloquea el cierre hasta cobrarla, quitar su última línea o descartarla; si un cobro y el cierre compiten, solo uno se confirma primero y la venta queda incluida en el esperado o es rechazada por turno cerrado, nunca confirmada fuera del cuadre (RN-10, RN-30).

<a id="HU-CAJA-02-CA-05"></a>

**HU-CAJA-02/CA-05.** Dado que el turno quedó cerrado, cuando se intenta vender con él, entonces el sistema rechaza la operación y permite que después se abra otro turno con nuevo dinero inicial, sin coexistencia de dos turnos abiertos (RN-10).

#### Casos de prueba escritos

<a id="CP-HU-CAJA-02-001"></a>
##### CP-HU-CAJA-02-001 · Cierre exacto, sobrante, faltante y rechazo

**Cubre:** HU-CAJA-02/CA-01, HU-CAJA-02/CA-02, HU-CAJA-02/CA-03, HU-CAJA-02/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** A turno 100+ventas 20=esperado 120 sin borrador; contado 120,125,115 en variantes; negativo/-1/abc/1.001; vendedor B.

1. Previsualizar y confirmar cierre con cada contado válido en fixture restaurado.
2. Reenviar cierre e intentar vender después.
3. Probar inválidos y B en fixtures propios.

**Resultados esperados:** Diferencia 0, +5, -5 respectivamente, acta inmutable con A/caja/fechas. Repetición rechaza sin reescribir; venta post cierre denegada. Inválidos/B no cierran. Nueva apertura posible solo tras cierre; esperado suma 20 no efectivo recibido 50.

<a id="CP-HU-CAJA-02-002"></a>
##### CP-HU-CAJA-02-002 · Borrador y cobro compiten con cierre

**Cubre:** HU-CAJA-02/CA-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Turno A100; borrador 2Leche=20; dos conexiones PG cobro/cierre 120.

1. Intentar cierre con borrador.
2. Cancelar o cobrar borrador y consultar.
3. Restaurar y sincronizar cobro/cierre; leer venta/stock/acta.

**Resultados esperados:** Borrador bloquea cierre hasta cobrar/quitar última línea/descartar. Carrera serial válida: venta incluida en esperado 120 o cierre rechaza mientras borrador; nunca venta confirmada fuera de acta. Si cierre ya confirmado, cobro rechaza sin mutación.

<a id="HU-CAJA-03"></a>

### HU-CAJA-03 · Caja — Registrar movimiento manual de efectivo

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero registrar ingresos o salidas manuales de efectivo en la caja durante mi turno, para justificar movimientos de dinero que no provienen de una venta.

**Reglas relacionadas:** RN-10, RN-11, RN-15. **Dependencias funcionales:** HU-CAJA-01.

**Orden de producto:** 40.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-09; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CAJA-03-CA-01"></a>

**HU-CAJA-03/CA-01.** Dado que registro un movimiento manual de efectivo, cuando indico el monto, entonces el sistema exige que sea mayor que cero y registrar obligatoriamente el motivo y el responsable de la operación (RN-11).

<a id="HU-CAJA-03-CA-02"></a>

**HU-CAJA-03/CA-02.** Dado que registro el movimiento en dinero en efectivo, cuando confirmo, entonces el sistema guarda la fecha, hora exacta y monto, reflejándolo en el resumen del turno.

<a id="HU-CAJA-03-CA-03"></a>

**HU-CAJA-03/CA-03.** Dado que los movimientos manuales son exclusivamente en efectivo, cuando intento seleccionar otra modalidad, entonces el sistema no lo permite (RN-15).

<a id="HU-CAJA-03-CA-04"></a>

**HU-CAJA-03/CA-04.** Dado que existen ingresos o salidas manuales confirmadas, cuando se calcula el dinero esperado al cerrar la caja, entonces se consideran sumando los ingresos manuales y restando las salidas manuales.

#### Casos de prueba escritos

<a id="CP-HU-CAJA-03-001"></a>
##### CP-HU-CAJA-03-001 · Movimientos manuales futuros

**Cubre:** HU-CAJA-03/CA-01, HU-CAJA-03/CA-02, HU-CAJA-03/CA-03, HU-CAJA-03/CA-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; vendedor dueño; turno 100+ventas 20; ingreso 10 motivo Cambio y salida 5 motivo Compra urgente; variantes 0/vacío/Yape.

1. Registrar ingreso 10 y salida 5.
2. Ver resumen y preparar cierre.
3. Probar monto 0, sin motivo y medio Yape.

**Resultados esperados:** Dos movimientos con autor/instante/monto; esperado 125. Inválidos rechazan sin asiento. Solo efectivo; no se presenta como cobro de venta ni duplica su total.

<a id="HU-CAJA-04"></a>

### HU-CAJA-04 · Caja — Ver resumen del turno activo

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero consultar en cualquier momento el resumen de cobros y movimientos de mi turno en curso, para conocer el saldo estimado en gaveta.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-CAJA-01, HU-VEN-01c y HU-CAJA-03.

**Orden de producto:** 41.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-09; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CAJA-04-CA-01"></a>

**HU-CAJA-04/CA-01.** Dado que tengo un turno abierto, cuando abro el resumen, entonces veo el monto inicial, el total de ventas cobradas, los movimientos manuales y el saldo estimado en efectivo.

<a id="HU-CAJA-04-CA-02"></a>

**HU-CAJA-04/CA-02.** Dado que se cobra una nueva venta o movimiento, cuando se actualiza la pantalla, entonces los totales reflejan el estado vigente sin necesidad de cerrar el turno.

#### Casos de prueba escritos

<a id="CP-HU-CAJA-04-001"></a>
##### CP-HU-CAJA-04-001 · Resumen futuro actualizado

**Cubre:** HU-CAJA-04/CA-01, HU-CAJA-04/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; turno A inicial 100, ventas 20, manual+10/-5; nueva venta 30.

1. Abrir resumen y después confirmar venta 30.
2. Actualizar resumen.

**Resultados esperados:** Primero inicial 100, ventas 20, manual neto 5, esperado 125; luego ventas 50, esperado 155. No suma efectivo antes del vuelto ni Yape a gaveta. Consulta no cierra turno.

<a id="HU-CAJA-05"></a>

### HU-CAJA-05 · Caja — Consultar historial de turnos de caja

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como ADMIN quiero consultar todos los turnos y como VENDEDOR solo los propios, incluidos los cerrados, con sus ventas y cuadres, para revisar diferencias sin acceder al dinero de otro empleado.

**Reglas relacionadas:** RN-10, RN-29. **Dependencias funcionales:** HU-CAJA-02.

**Orden de producto:** 18.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-12-PERMISOS-HISTORIAL-Y-MENU](#contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU), [DEC-12-ORDEN-LINEAS-RECIBO](#contrato-DEC-12-ORDEN-LINEAS-RECIBO).

#### Criterios de aceptación

<a id="HU-CAJA-05-CA-01"></a>

**HU-CAJA-05/CA-01.** Dado que accedo al historial de turnos autorizado (ADMIN global, VENDEDOR solo propios), cuando la lista carga, entonces veo por cada turno: vendedor, fechas y horas de apertura y cierre, dinero inicial, total cobrado, dinero declarado y diferencia.

<a id="HU-CAJA-05-CA-02"></a>

**HU-CAJA-05/CA-02.** Dado que aplico rango de fechas y, solo como ADMIN, filtro por vendedor, cuando consulto, entonces muestra turnos correspondientes sin ampliar el conjunto autorizado ni permitir acceso directo a un turno ajeno.

#### Casos de prueba escritos

<a id="CP-HU-CAJA-05-001"></a>
##### CP-HU-CAJA-05-001 · Historia propia/global y filtros

**Cubre:** HU-CAJA-05/CA-01, HU-CAJA-05/CA-02. **Estado:** EJECUTADO EN MUESTRA AISLADA (12-B, 14/11/2026) — CUMPLE en SQLite, Chrome (`VENDEDOR` + `ADMIN`) y PostgreSQL `18.4` (26 turnos con empate temporal, paginación 25/página con filtros preservados, `Total cobrado`, `<h1>` «Acta de cierre», móvil `390×844` e impresión). No cubre `PG 17`, `SIGKILL` ni despliegue en base operativa.
**Evidencia de ejecución:** [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b) · [Suite 12](auditoria_por_etapas/resultados/evidencias/12-tests-20261115T024447678082Z-34890834/test_output.txt) · [Chrome 12](auditoria_por_etapas/resultados/evidencias/12-browser-20261115T024214133045Z-c16c172f/browser-report.json) · [PG 18.4](auditoria_por_etapas/resultados/evidencias/12-pg-20261115T024551489938Z-daa4b807/pg-report.json).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** A turno cerrado 12/11 inicial 100, ventas 20, contado 115, diferencia-5; Bturno 11/11; ADMIN; 26 turnos con empate instante.

1. Consultar A y ADMIN.
2. Filtrar 12/11 y vendedor A como ADMIN.
3. Como A alterar filtro/ID a B; paginar.

**Resultados esperados:** A solo propios; ADMIN global/filtro exacto. Columnas incluyen apertura/cierre/inicial/cobrado/declarado/diferencia. I Ds/filtros no amplían permiso. Orden estable con desempate ID,25/página ysin omitir/duplicar empatados.

<a id="HU-CAJA-06"></a>

### HU-CAJA-06 · Caja — Aprobar cierre de turno

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero revisar y validar formalmente el cuadre de un turno cerrado, para dejar constancia de la conformidad administrativa.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-CAJA-02.

**Orden de producto:** 42.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-09; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CAJA-06-CA-01"></a>

**HU-CAJA-06/CA-01.** Dado un turno cerrado, cuando ADMIN revisa y aprueba el cierre, entonces registra el estado de revisión Aprobado, autor e instante sin modificar el cierre original, sus importes ni su condición irreversible; no reabre el turno.

<a id="HU-CAJA-06-CA-02"></a>

**HU-CAJA-06/CA-02.** Dado un cierre con sobrante o faltante, cuando ADMIN lo aprueba, entonces exige y conserva una observación de revisión junto con la diferencia original, sin convertirla artificialmente en cero.

#### Casos de prueba escritos

<a id="CP-HU-CAJA-06-001"></a>
##### CP-HU-CAJA-06-001 · Aprobación futura conserva el cierre original

**Cubre:** HU-CAJA-06/CA-01, HU-CAJA-06/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; turno A cerrado esperado 120 contado 115 diferencia-5; ADMIN; observación Faltante revisado.

1. Aprobar cierre y consultar acta original y revisión.
2. Intentar cambiar contado/reabrir desde aprobación.

**Resultados esperados:** Estado de revisión Aprobado con ADMIN/fecha/observación y diferencia-5; cierre sigue irreversible y valores originales 120/115/-5. No reabre caja ni convierte faltante en 0.

<a id="HU-CAJA-07"></a>

### HU-CAJA-07 · Caja – Forzar cierre de turno de caja

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero forzar el cierre administrativo de un turno de caja abandonado tras 2 horas o más de inactividad, para liberar la caja y regularizar la operación.

**Reglas relacionadas:** RN-23. **Dependencias funcionales:** HU-CAJA-01.

**Orden de producto:** 43.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-09; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CAJA-07-CA-01"></a>

**HU-CAJA-07/CA-01.** Dado que un turno de caja no registra ventas ni movimientos durante 2 horas consecutivas o más (RN-23), cuando el administrador consulta la caja, entonces el sistema habilita la opción de Cierre Forzado Administrativo.

<a id="HU-CAJA-07-CA-02"></a>

**HU-CAJA-07/CA-02.** Dado un turno elegible por inactividad, cuando ADMIN confirma su cierre forzado con motivo, entonces registra cierre administrativo, ventas acumuladas y autor y libera la caja sin inventar un arqueo; si no se contó efectivo, el contado y la diferencia se indican como No declarado. La política de borradores y carreras se refina antes de seleccionar esta función futura.

#### Casos de prueba escritos

<a id="CP-HU-CAJA-07-001"></a>
##### CP-HU-CAJA-07-001 · Cierre forzado futuro sin inventar arqueo

**Cubre:** HU-CAJA-07/CA-01, HU-CAJA-07/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; turno última operación 10:00 Lima esperado 120; reloj 11:59:59 y 12:00; sin recuento físico aportado.

1. Consultar opción antes y al cumplir 2 h.
2. Confirmar al umbral con motivo y revisar resumen.

**Resultados esperados:** Antes 2 h no habilitado; al cumplir permite cierre administrativo trazable. Libera caja y conserva ventas; contado/diferencia constan NO DECLARADO si no hay arqueo, nunca inventa 120/0. Borrador/cobro concurrente requiere refinamiento transaccional antes de desarrollar.

<a id="HU-VEN-01a"></a>

### HU-VEN-01a · Ventas — Bloquear la pantalla de venta por inactividad

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 8 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero que la pantalla de venta se bloquee tras 5 minutos de inactividad, para evitar que terceros operen la caja cuando me alejo del mostrador.

**Reglas relacionadas:** RN-22. **Dependencias funcionales:** HU-CAJA-01.

**Orden de producto:** 19.

**Estimación:** Bloqueo en servidor compartido por pestañas y reautenticación con validación de estado.

**Procedencia:** ETAPA-10; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-10-BLOQUEO-INACTIVIDAD](#contrato-DEC-10-BLOQUEO-INACTIVIDAD).

#### Criterios de aceptación

<a id="HU-VEN-01a-CA-01"></a>

**HU-VEN-01a/CA-01.** Dado que la pantalla de venta permanece sin uso durante 5 minutos continuos, cuando se cumple dicho tiempo, entonces se bloquea automáticamente protegiendo la caja (RN-22).

<a id="HU-VEN-01a-CA-02"></a>

**HU-VEN-01a/CA-02.** Dado que la pantalla está bloqueada, cuando intento cualquier acción, entonces el sistema me exige reingresar mi contraseña.

<a id="HU-VEN-01a-CA-03"></a>

**HU-VEN-01a/CA-03.** Dado que reingreso mi contraseña correcta, cuando el sistema la valida, entonces regreso a la pantalla de venta conservando la venta en curso sin pérdida de datos.

#### Casos de prueba escritos

<a id="CP-HU-VEN-01a-001"></a>
##### CP-HU-VEN-01a-001 · Bloqueo de puesto a 300 segundos

**Cubre:** HU-VEN-01a/CA-01, HU-VEN-01a/CA-02, HU-VEN-01a/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** A turno abierto, borrador 2Leche; reloj servidor controlado; 2 pestañas; claves errónea/correcta y cuenta B.

1. Dejar 299 s y consultar; avanzar 300 s sin actividad humana.
2. Intentar consultar/cobrar por otra pestaña y POST directo.
3. Enviar clave errónea y credenciales B.
4. Reautenticar con A correcta.

**Resultados esperados:** A300 s servidor bloquea datos/operaciones; polling/relojdelcliente no evitan bloqueo. Error/B no desbloquea ni borra borrador. A correcta recupera borrador/turno y revalida precio/stock antes de cobrar. No equivale a cerrar sesión/caja.

<a id="HU-VEN-01b"></a>

### HU-VEN-01b · Preparar una venta y revisar existencias

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero buscar productos, indicar cantidades y revisar las existencias disponibles antes de cobrar, para atender al cliente en mostrador con los precios y totales claros.

**Reglas relacionadas:** RN-03, RN-10, RN-27, RN-29, RN-30. **Dependencias funcionales:** HU-CAJA-01 y HU-INV-01a.

**Orden de producto:** 6.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-10; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-11-DESCUENTOS-ALCANCE](#contrato-DEC-11-DESCUENTOS-ALCANCE), [DEC-10-BLOQUEO-INACTIVIDAD](#contrato-DEC-10-BLOQUEO-INACTIVIDAD), [DEC-11-TOPE-EFECTIVO-FORM](#contrato-DEC-11-TOPE-EFECTIVO-FORM), [DEC-12-ORDEN-LINEAS-RECIBO](#contrato-DEC-12-ORDEN-LINEAS-RECIBO).

#### Criterios de aceptación

<a id="HU-VEN-01b-CA-01"></a>

**HU-VEN-01b/CA-01.** Dado que ingreso con rol `VENDEDOR`, cuando inicio la preparación y agrego la primera línea válida, entonces el sistema exige un turno abierto ligado a mi propio usuario y crea la venta en preparación; cualquier otro rol o vendedor sin ese turno recibe una denegación (RN-10, RN-29, RN-30).

<a id="HU-VEN-01b-CA-02"></a>

**HU-VEN-01b/CA-02.** Dado que preparo la venta, cuando busco un producto activo de cualquier categoría activa del alcanceUND/vencimiento, por nombre o digitando su código de barras, entonces puedo seleccionarlo si posee existencias vendibles, sin requerir lector físico para esta consultaPOS; el lector del altaPROD03 tiene su propio contrato.

<a id="HU-VEN-01b-CA-03"></a>

**HU-VEN-01b/CA-03.** Dado que agrego o actualizo un producto, cuando indico la cantidad, entonces exige un entero mayor que cero, agrupa el mismo producto en una sola línea y rechaza un total superior a sus existencias vendibles.

<a id="HU-VEN-01b-CA-04"></a>

**HU-VEN-01b/CA-04.** Dado que un lote vence hoy o ya venció según la fecha de `America/Lima`, cuando el sistema calcula las existencias vendibles, entonces excluye todas sus unidades y nunca las ofrece para completar la cantidad solicitada (RN-03).

<a id="HU-VEN-01b-CA-05"></a>

**HU-VEN-01b/CA-05.** Dado que la lista contiene líneas, cuando reviso la venta, entonces se considera una venta en preparación que aún no reserva ni descuenta stock ni mueve efectivo; muestra precio unitario, cantidad, importe por línea, total y el desglose `base = HALF_UP(total / 1.18, 2)` e `IGV = total - base`. Si quito la última línea, el borrador se descarta y deja de bloquear el cierre; al descartarlo, caja y existencias quedan intactas (RN-27, RN-30).

#### Casos de prueba escritos

<a id="CP-HU-VEN-01b-001"></a>
##### CP-HU-VEN-01b-001 · Borrador agrupa, calcula y no reserva

**Cubre:** HU-VEN-01b/CA-01, HU-VEN-01b/CA-02, HU-VEN-01b/CA-03, HU-VEN-01b/CA-04, HU-VEN-01b/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** A dueño turno; Leche precio 10,20 vigentes; producto inactivo; E3 vencidas en producto separado; búsqueda Leche/códigoINT-LECHE-1.

1. Buscar y agregar 1Lechedosveces.
2. Revisar totales y tablas.
3. Probar cantidad 21/0/1.5 y producto E/inactivo; actor es B/ADMIN.
4. Quitar última línea.

**Resultados esperados:** Una línea 2×10=20, base 16.95, IGV3.05; stock 20 y caja 100 intactos. Exc esos, fracciones, vencidos/inactivos y roles ajenos rechazan. Quitar última línea descarta borrador y deja de bloquear cierre, sin venta/correlativo.

<a id="HU-VEN-01c"></a>

### HU-VEN-01c · Cobrar en efectivo y descontar existencias

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 13 (orientativos; anteriores:5).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero cobrar la venta en efectivo, calcular el vuelto y descontar la mercadería de los lotes adecuados, para completar la atención y mantener el inventario al día.

**Reglas relacionadas:** RN-03, RN-10, RN-19, RN-25, RN-27, RN-28, RN-29, RN-30. **Dependencias funcionales:** HU-VEN-01b.

**Orden de producto:** 7.

**Estimación:** Venta atómica con asignaciones, snapshots, idempotencia, política de descuentos y concurrencia real.

**Procedencia:** ETAPA-11; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AH-01](#contrato-DOC-03AH-01), [DEC-11-MODELO-AUDITORIA-VENTAS](#contrato-DEC-11-MODELO-AUDITORIA-VENTAS), [DEC-11-DESCUENTOS-ALCANCE](#contrato-DEC-11-DESCUENTOS-ALCANCE), [DEC-08-KARDEX-COMPRAS](#contrato-DEC-08-KARDEX-COMPRAS), [DEC-11-TOPE-EFECTIVO-FORM](#contrato-DEC-11-TOPE-EFECTIVO-FORM), [CT-ROLLBACK-01-POST-ESCRITURA](#contrato-CT-ROLLBACK-01-POST-ESCRITURA).

#### Criterios de aceptación

<a id="HU-VEN-01c-CA-01"></a>

**HU-VEN-01c/CA-01.** Dado que una venta en preparación tiene líneas y el efectivo ingresado es no numérico, tiene más de dos decimales o resulta menor que el total, cuando intento cobrar, entonces el sistema rechaza la operación, informa el faltante cuando corresponda y no crea venta, correlativo o movimiento ni modifica existencias (RN-30).

<a id="HU-VEN-01c-CA-02"></a>

**HU-VEN-01c/CA-02.** Dado que ingreso un efectivo válido igual o mayor al total, cuando confirmo, entonces el sistema calcula `vuelto = efectivo recibido - total` con dos decimales y aumenta el efectivo esperado solo por el total vendido, no por el efectivo recibido antes del vuelto (RN-10, RN-27).

<a id="HU-VEN-01c-CA-03"></a>

**HU-VEN-01c/CA-03.** Dado que mi turno sigue abierto y existe stock suficiente al confirmar, cuando se descuentan unidades, entonces el sistema revalida las condiciones y aplica FEFO por vencimiento, instante de ingreso e identificador interno, continúa por los lotes vigentes necesarios y nunca deja existencias negativas (RN-03, RN-19, RN-29).

<a id="HU-VEN-01c-CA-04"></a>

**HU-VEN-01c/CA-04.** Dado que el cobro se procesa, cuando la operación termina, entonces venta, detalles históricos, asignaciones de lotes, movimiento de efectivo, descuento de existencias y correlativo global `V-00000001` se confirman juntos; ante cualquier fallo no se confirma ninguna parte (RN-25).

<a id="HU-VEN-01c-CA-05"></a>

**HU-VEN-01c/CA-05.** Dado que se produce doble clic, reenvío, reintento o competencia por las últimas unidades, cuando el sistema procesa las solicitudes, entonces un mismo intento lógico genera como máximo una venta, un movimiento, un correlativo y un descuento, y solo cobran las operaciones para las que existe stock confirmado (RN-25).

<a id="HU-VEN-01c-CA-06"></a>

**HU-VEN-01c/CA-06.** Dado que la venta queda confirmada, cuando se guarda su fotografía histórica, entonces conserva nombre del producto, cantidad, precio con dos decimales, costo promedio con cuatro decimales, importes, efectivo y vuelto; cambios posteriores del catálogo o del costo no alteran esos valores (RN-28).

#### Casos de prueba escritos

<a id="CP-HU-VEN-01c-001"></a>
##### CP-HU-VEN-01c-001 · Cobro en efectivo atómico e histórico

**Cubre:** HU-VEN-01c/CA-02, HU-VEN-01c/CA-03, HU-VEN-01c/CA-04, HU-VEN-01c/CA-06. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** A turno 100; borrador 2Leche×10;A10@2/B10@4, promedio 3; efectivo recibido 50.

1. Confirmar cobro.
2. Inspeccionar venta, líneas, asignaciones lote, movimiento, contador y stock.
3. Cambiar nombre/precio/costo/nombre vendedor/caja y abrir constancia.

**Resultados esperados:** Una venta 20, vuelto 30, base 16.95, IGV3.05, caja esperada 120; stock A8/B10, total 18; asignación A2, costo histórico 3.0000, promedio vigente 3. V-00000001 si contador 0; snapshots originales intactos, incluida identidad visible vendedor/caja. No costos en constancia.

<a id="CP-HU-VEN-01c-002"></a>
##### CP-HU-VEN-01c-002 · Cobro rechazado y reintento concurrente

**Cubre:** HU-VEN-01c/CA-01, HU-VEN-01c/CA-03, HU-VEN-01c/CA-04, HU-VEN-01c/CA-05. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Borrador 20; efectivo 19.99/abc/20.001; variantes stock insuficiente por otro servicio y dos conexiones PG con misma clave válida.

1. Probar inválidos y capturar estado completo antes/después.
2. Sincronizar doble cobro 50 con misma clave.
3. Inyectar fallo después de descontar el primer lote y antes del commit.

**Resultados esperados:** Inválidos rechazan sin venta/correlativo/caja ni stock. Doble cobro devuelve una venta/constancia y descuento de 2 unidades. Fallo post escritura revierte todo; si respuesta se pierde tras commit, reintento recupera resultado. Documentar barrera y conexiones.

<a id="HU-VEN-02a"></a>

### HU-VEN-02a · Generar una constancia interna de venta

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero generar una constancia interna numerada de la venta cobrada, para entregar al cliente un respaldo de su compra y mantener el control interno del minimarket.

**Reglas relacionadas:** RN-26, RN-27, RN-29. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 8.

**Estimación:** Snapshots de vendedor/caja, orden de líneas y navegación/impresión coherente.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-11-MODELO-AUDITORIA-VENTAS](#contrato-DEC-11-MODELO-AUDITORIA-VENTAS), [DEC-11-DESCUENTOS-ALCANCE](#contrato-DEC-11-DESCUENTOS-ALCANCE), [DEC-12-PERMISOS-HISTORIAL-Y-MENU](#contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU), [DEC-12-ORDEN-LINEAS-RECIBO](#contrato-DEC-12-ORDEN-LINEAS-RECIBO).

#### Criterios de aceptación

<a id="HU-VEN-02a-CA-01"></a>

**HU-VEN-02a/CA-01.** Dado que la venta fue confirmada con un correlativo global `V-00000001`, cuando se genera la constancia, entonces reutiliza exactamente ese número sin asignar otro y ofrece al vendedor verla en pantalla y abrir una vista preparada para la impresión del navegador (RN-26).

<a id="HU-VEN-02a-CA-02"></a>

**HU-VEN-02a/CA-02.** Dado que reviso la constancia, cuando carga su contenido histórico, entonces muestra fecha y hora de Lima, vendedor, caja, nombre de cada producto, cantidad, precio e importe, base, IGV, total, efectivo y vuelto, pero nunca muestra el costo de compra o costo promedio (RN-26, RN-27).

<a id="HU-VEN-02a-CA-03"></a>

**HU-VEN-02a/CA-03.** Dado que la constancia se visualiza o imprime, cuando se lee, entonces exhibe «CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO», sin logotipos ni leyendas de aprobación SUNAT y sin afirmar que ya se emitió o entregó una boleta/factura externa. El canal autorizado real se debe confirmar antes del piloto (RN-26).

<a id="HU-VEN-02a-CA-04"></a>

**HU-VEN-02a/CA-04.** Dado que el vendedor usa «Última constancia» desde la pantalla de venta de su turno, cuando la vuelve a abrir, entonces recupera el mismo correlativo y los mismos datos históricos aunque el catálogo cambie; un rol no autorizado no puede consultarla mediante acceso directo (RN-26, RN-29).

#### Casos de prueba escritos

<a id="CP-HU-VEN-02a-001"></a>
##### CP-HU-VEN-02a-001 · Constancia histórica e impresión fiel

**Cubre:** HU-VEN-02a/CA-01, HU-VEN-02a/CA-02, HU-VEN-02a/CA-03, HU-VEN-02a/CA-04. **Estado:** EJECUTADO EN MUESTRA AISLADA (12-B, 14/11/2026) — CUMPLE en SQLite, Chrome (`1366×900`, `390×844`, `@media print`) y PostgreSQL `18.4` (correlativo `V-00000001..N`, snapshots sin costos para ningún rol, orden de líneas persistido + aviso legado, leyenda SUNAT, reintento idempotente, enlace «Última constancia» y aislamiento por rol). No cubre impresora térmica física, `PG 17` ni base operativa.
**Evidencia de ejecución:** [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b) · [Suite 12](auditoria_por_etapas/resultados/evidencias/12-tests-20261115T024447678082Z-34890834/test_output.txt) · [Chrome móvil](auditoria_por_etapas/resultados/evidencias/12-browser-20261115T024214133045Z-c16c172f/mobile-receipt-390x844.png) · [PG 18.4](auditoria_por_etapas/resultados/evidencias/12-pg-20261115T024551489938Z-daa4b807/pg-report.json).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** Venta V-00000001A2Leche×10, total 20, efectivo 50, vuelto 30; ADMIN, A, B, ALMACENERO; catálogo posteriormente editado.

1. Abrir constancia y Última constancia como A.
2. Abrir vista impresión y comparar campos.
3. Probar I Ds directos como B/ALMACENERO y consulta ADMIN.

**Resultados esperados:** Mismo correlativo y datos originales, Lima, vendedor, caja, líneas, base 16.95, IGV3.05, total 20, efectivo 50, vuelto 30; sin costos para ningunrol. Le y en da CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO visible también al imprimir; no afirma emisión electrónica externa verificada. B/ALMACENERO denegados.

<a id="HU-VEN-04"></a>

### HU-VEN-04 · Ventas – Buscar producto por código de barras

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero leer el código de barras de un producto en el mostrador para consultar de inmediato su precio y existencias, para responder rápido al cliente sin alterar la venta en curso.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01b.

**Orden de producto:** 73.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-10; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-VEN-04-CA-01"></a>

**HU-VEN-04/CA-01.** Dado que paso el código de barras de un producto por el lector en la consulta rápida, cuando el sistema lo reconoce, entonces muestra nombre, precio vigente y existencias vendibles sin agregarlo a la lista de venta.

<a id="HU-VEN-04-CA-02"></a>

**HU-VEN-04/CA-02.** Dado que el código de barras leído no pertenece a ningún producto registrado, cuando se busca, entonces muestra «Producto no encontrado».

#### Casos de prueba escritos

<a id="CP-HU-VEN-04-001"></a>
##### CP-HU-VEN-04-001 · Consulta rápida futura sin agregar

**Cubre:** HU-VEN-04/CA-01, HU-VEN-04/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; VENDEDOR sin turno; Leche códigoINT-LECHE-1 precio 10 vendible 20; no existenteINT-XXX.

1. Leer código existente y no existente en consulta rápida.
2. Inspeccionar borradores/stock/caja.

**Resultados esperados:** Existente muestra nombre/precio 10/vendible 20 sin crear venta; búsqueda fallida Producto no encontrado. No exponer costos ni implicar permiso actual POS sin turno.

<a id="HU-VEN-05a"></a>

### HU-VEN-05a · Ventas — Consultar las ventas de mi turno

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero consultar las ventas confirmadas de mi turno activo, para verificar los cobros realizados y facilitar el cuadre antes de cerrar la caja.

**Reglas relacionadas:** RN-07. **Dependencias funcionales:** HU-VEN-01c y HU-CAJA-01.

**Orden de producto:** 16.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-12-PERMISOS-HISTORIAL-Y-MENU](#contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU), [DEC-12-ORDEN-LINEAS-RECIBO](#contrato-DEC-12-ORDEN-LINEAS-RECIBO).

#### Criterios de aceptación

<a id="HU-VEN-05a-CA-01"></a>

**HU-VEN-05a/CA-01.** Dado que tengo un turno de caja abierto, cuando consulto las ventas, entonces veo únicamente las operaciones confirmadas por mi usuario en el turno en curso (RN-07).

<a id="HU-VEN-05a-CA-02"></a>

**HU-VEN-05a/CA-02.** Dado que reviso la lista de ventas del turno, cuando consulto los totales acumulados, entonces el total en efectivo coincide con los registros confirmados; los canales digitales no se presentan como disponibles hasta seleccionar e implementar HU-VEN-07.

#### Casos de prueba escritos

<a id="CP-HU-VEN-05a-001"></a>
##### CP-HU-VEN-05a-001 · Ventas del turno y suma

**Cubre:** HU-VEN-05a/CA-01, HU-VEN-05a/CA-02. **Estado:** EJECUTADO EN MUESTRA AISLADA (12-B, 14/11/2026) — CUMPLE en SQLite, Chrome (`1366×768`) y pruebas de rol (`ADMIN`/`ALMACENERO` `403`, excluye turnos previos y ventas ajenas, efectivo sin anunciar `Yape`). No cubre `PG 17` ni base operativa.
**Evidencia de ejecución:** [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b) · [Suite 12](auditoria_por_etapas/resultados/evidencias/12-tests-20261115T024447678082Z-34890834/test_output.txt) · [Chrome 12](auditoria_por_etapas/resultados/evidencias/12-browser-20261115T024214133045Z-c16c172f/post-fix-sales-shift-history-1366x768.png).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** A turno actual ventas 20 y 30; A turno anterior 10; Bventa 40; ADMIN.

1. Como A abrir Mis ventas.
2. Revisar suma y alterar parámetros a turno previo/B.

**Resultados esperados:** Turno actual solo 20 y 30, suma efectivo 50; otros turnos/usuarios no filtran datos al turno actual. No anuncia Yape disponible en R1. ADMIN consulta global por historial autorizado.

<a id="HU-VEN-05b"></a>

### HU-VEN-05b · Ventas — Consultar el historial de ventas con filtros

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 5 (orientativos; anteriores:3).

**Alcance:** R1 seleccionado; especificación ACEPTADA. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero consultar el historial general de ventas confirmadas aplicando filtros por fecha, vendedor y turno, para supervisar las operaciones de la bodega.

**Reglas relacionadas:** RN-07. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 17.

**Estimación:** Propiedad de datos, filtros, totales y paginación estable.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-12-PERMISOS-HISTORIAL-Y-MENU](#contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU), [DEC-12-ORDEN-LINEAS-RECIBO](#contrato-DEC-12-ORDEN-LINEAS-RECIBO).

#### Criterios de aceptación

<a id="HU-VEN-05b-CA-01"></a>

**HU-VEN-05b/CA-01.** Dado que ingreso como administrador o dueño, cuando abro el historial de ventas, entonces visualizo las ventas confirmadas registradas por todos los empleados (RN-07).

<a id="HU-VEN-05b-CA-02"></a>

**HU-VEN-05b/CA-02.** Dado que aplico filtros por rango de fechas, vendedor o turno, cuando consulto, entonces la pantalla muestra únicamente las operaciones que cumplen los criterios.

<a id="HU-VEN-05b-CA-03"></a>

**HU-VEN-05b/CA-03.** Dado que selecciono una venta de la lista, cuando abro su detalle completo, entonces veo productos, cantidades, precios, base imponible, IGV, total, medio de pago y constancia interna.

#### Casos de prueba escritos

<a id="CP-HU-VEN-05b-001"></a>
##### CP-HU-VEN-05b-001 · Historial con filtros y detalle

**Cubre:** HU-VEN-05b/CA-01, HU-VEN-05b/CA-02, HU-VEN-05b/CA-03. **Estado:** EJECUTADO EN MUESTRA AISLADA (12-B, 14/11/2026) — CUMPLE en SQLite, Chrome (`1366×768` + `390×844`) y PostgreSQL `18.4` (filtros Lima, `\x00`/rangos/página inválidos sin `500`, aislamiento `VENDEDOR`, paginación 25/página en 26 ventas empatadas con total filtrado íntegro y enlace a constancia). No cubre `PG 17`, SLA productivo ni base operativa.
**Evidencia de ejecución:** [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b) · [Suite 12](auditoria_por_etapas/resultados/evidencias/12-tests-20261115T024447678082Z-34890834/test_output.txt) · [Chrome 12](auditoria_por_etapas/resultados/evidencias/12-browser-20261115T024214133045Z-c16c172f/browser-report.json) · [PG 18.4](auditoria_por_etapas/resultados/evidencias/12-pg-20261115T024551489938Z-daa4b807/pg-report.json).
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** ADMIN; A venta 20 el 12/11 en T1 y 10 el 11/11T0; Bventa 30 el 12/11T2; 26 ventas para paginación.

1. Abrir global y filtrar 12/11, vendedor A, T1.
2. Abrir venta de 20.
3. Probar fecha incompleta/invertida, qcon NUL yrol A para I Dde B.
4. Navegar páginas con mismos filtros.

**Resultados esperados:** Filtro por intersección devuelve venta 20; detalle líneas/base 16.95/IGV3.05/total 20/efectivo/constancia. Inválidos muestran error sin 500; A no accede a B. Paginación 25 estable; totales sobre conjunto filtrado, no solo página; no exige expandir líneas dentro de la lista.

<a id="HU-VEN-06a"></a>

### HU-VEN-06a · Ventas — Anular una venta cobrada en efectivo

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero anular una venta cobrada en efectivo de un turno abierto, para corregir errores de mostrador y devolver el dinero sin descuadrar la caja.

**Reglas relacionadas:** RN-08, RN-10. **Dependencias funcionales:** HU-VEN-01c y HU-VEN-02a.

**Orden de producto:** 36.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-VEN-06a-CA-01"></a>

**HU-VEN-06a/CA-01.** Dado que la venta pertenece a un turno de caja abierto, cuando el administrador autoriza la anulación indicando el motivo justificado, entonces la venta pasa a estado Anulada y se emite la constancia interna de anulación.

<a id="HU-VEN-06a-CA-02"></a>

**HU-VEN-06a/CA-02.** Dado que la venta fue cobrada en efectivo, cuando se confirma la anulación, entonces el sistema descuenta dicho monto del dinero esperado del turno activo.

<a id="HU-VEN-06a-CA-03"></a>

**HU-VEN-06a/CA-03.** Dado que el turno de caja ya se encuentra cerrado o con cierre forzado, cuando intento anular una venta de ese turno, entonces el sistema bloquea la operación conforme a la regla RN-08.

#### Casos de prueba escritos

<a id="CP-HU-VEN-06a-001"></a>
##### CP-HU-VEN-06a-001 · Anulación futura de efectivo

**Cubre:** HU-VEN-06a/CA-01, HU-VEN-06a/CA-02, HU-VEN-06a/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; venta 20 en A turno abierto esperado 120; motivo Error de despacho; variante cerrado.

1. Anular con motivo y consultar venta/constancia/caja.
2. Reintentar.
3. Restaurar y cerrar turno antes de anular.

**Resultados esperados:** Venta Anulada, constancia de anulación vinculada; esperado 100 tras reembolso 20 confirmado; no borra venta original. Reintento no duplica devolución; cerrado rechaza sin cambios. Destino de unidades exige VEN06 c.

<a id="HU-VEN-06b"></a>

### HU-VEN-06b · Ventas — Anular una venta cobrada con Yape

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero anular una venta cobrada con billetera digital Yape registrando los datos de anulación, para respaldar el reintegro al cliente.

**Reglas relacionadas:** RN-08. **Dependencias funcionales:** HU-VEN-06a y HU-VEN-07.

**Orden de producto:** 39.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-VEN-06b-CA-01"></a>

**HU-VEN-06b/CA-01.** Dado que la venta fue cobrada con Yape en un turno abierto, cuando el administrador confirma la anulación, entonces el sistema registra la anulación capturando el código de autorización original y el motivo.

<a id="HU-VEN-06b-CA-02"></a>

**HU-VEN-06b/CA-02.** Dado que se finaliza la anulación de una venta digital, cuando el sistema la procesa, entonces emite la constancia interna de anulación indicando que no afecta el efectivo físico en gaveta.

#### Casos de prueba escritos

<a id="CP-HU-VEN-06b-001"></a>
##### CP-HU-VEN-06b-001 · Anulación futura digital sin tocar gaveta

**Cubre:** HU-VEN-06b/CA-01, HU-VEN-06b/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; venta Yape 20 código YP-TEST-001 en turno abierto; caja esperada 100.

1. Anular con motivo y revisar constancia/caja/código original.

**Resultados esperados:** Anulación con motivo/código original vinculado; caja esperada 100 intacta. Constancia indica sin efecto físico; no afirma que el software ejecutó un reembolso externo sin integración comprobada.

<a id="HU-VEN-06c"></a>

### HU-VEN-06c · Ventas — Definir el destino de la mercadería devuelta

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como encargado del almacén o administrador, quiero calificar los productos de una venta anulada para regresarlos al stock o enviarlos a merma, para mantener el inventario correcto.

**Reglas relacionadas:** RN-09. **Dependencias funcionales:** HU-VEN-06a y HU-INV-02.

**Orden de producto:** 37.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-VEN-06c-CA-01"></a>

**HU-VEN-06c/CA-01.** Dadas unidades devueltas íntegras y todavía vigentes, cuando se confirma una anulación autorizada, entonces regresan al lote original identificado en la venta; las vencidas nunca se ofrecen como vendibles. El destino de devoluciones vencidas y los requisitos de evidencia se refinan antes de seleccionar esta función futura (RN-09).

<a id="HU-VEN-06c-CA-02"></a>

**HU-VEN-06c/CA-02.** Dado que los productos devueltos presentan daños, abolladuras o están abiertos, cuando se procesa la anulación, entonces se derivan directamente a baja por merma (RN-09).

<a id="HU-VEN-06c-CA-03"></a>

**HU-VEN-06c/CA-03.** Dado que se define el destino de la mercadería, cuando consulto los movimientos del producto, entonces visualizo el reingreso o la baja con su responsable.

#### Casos de prueba escritos

<a id="CP-HU-VEN-06c-001"></a>
##### CP-HU-VEN-06c-001 · Devolución futura conserva lote y destino

**Cubre:** HU-VEN-06c/CA-01, HU-VEN-06c/CA-02, HU-VEN-06c/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; venta 2Leche asigna da a lote A; devolución 1 íntegra/1 envase abierto; variante lote A vence hoy.

1. Procesar devolución con decisión ADMIN por línea.
2. Consultar movimientos y stock vendible.
3. Restaurar y probar íntegra pero ya vencida.

**Resultados esperados:** Íntegra vigente retorna al lote original; dañada registra baja vinculada sin ofrecer a la venta. Responsable/origen/destino visibles. Vencida no se ofrece como vendible; destino requiere política futura refinada, nunca aplicar FEFO actual para inventar lote original.

<a id="HU-VEN-07"></a>

### HU-VEN-07 · Cobrar con Yape y registrar el código de operación

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como vendedor, quiero registrar el cobro realizado con Yape ingresando el código de operación tras comprobar el ingreso del dinero en el teléfono de la bodega, para asentar la venta como pagada y entregar la constancia al cliente.

**Reglas relacionadas:** RN-02. **Dependencias funcionales:** HU-VEN-01b y HU-VEN-01c.

**Orden de producto:** 38.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-12; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-VEN-07-CA-01"></a>

**HU-VEN-07/CA-01.** Dado que el cliente paga con Yape, cuando el vendedor revisa fuera del sistema en el teléfono o medio habitual de la bodega y declara haber comprobado que el dinero realmente llegó, entonces el sistema habilita el registro del cobro con Yape (RN-02).

<a id="HU-VEN-07-CA-02"></a>

**HU-VEN-07/CA-02.** Dado que el vendedor intenta confirmar el cobro sin declarar que comprobó el ingreso del dinero en Yape, cuando pulsa el botón de confirmar, entonces el sistema no confirma la venta y solicita verificar primero el abono en el teléfono del minimarket.

<a id="HU-VEN-07-CA-03"></a>

**HU-VEN-07/CA-03.** Dado que se procede al cobro con Yape, cuando el vendedor ingresa los datos, entonces el código de operación es obligatorio y debe escribirse completo tal como aparece en la operación de Yape, impidiendo guardar la venta si el campo queda vacío.

<a id="HU-VEN-07-CA-04"></a>

**HU-VEN-07/CA-04.** Dado que se ingresa un código de operación que ya fue utilizado en una venta anterior, cuando se intenta confirmar el cobro, entonces el sistema advierte que el código ya fue registrado e impide utilizarlo nuevamente (RN-02).

<a id="HU-VEN-07-CA-05"></a>

**HU-VEN-07/CA-05.** Dado que el vendedor declaró haber comprobado el ingreso y escribió un código de operación no utilizado previamente, cuando confirma la operación, entonces la venta queda registrada como pagada con Yape y se descuentan las existencias de mercadería.

<a id="HU-VEN-07-CA-06"></a>

**HU-VEN-07/CA-06.** Dado que la venta con Yape queda registrada como pagada, cuando concluye la transacción, entonces la venta conserva el código de operación junto con el registro y genera su constancia interna de venta para el cliente y el control del negocio.

#### Casos de prueba escritos

<a id="CP-HU-VEN-07-001"></a>
##### CP-HU-VEN-07-001 · Cobro Yape futuro con comprobación humana

**Cubre:** HU-VEN-07/CA-01, HU-VEN-07/CA-02, HU-VEN-07/CA-03, HU-VEN-07/CA-04, HU-VEN-07/CA-05, HU-VEN-07/CA-06. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; vendedor A dueño; borrador 20; código YP-TEST-001 nuevo; código YP-TEST-000 yausado; variantes declaración no/si y código vacío.

1. Intentar confirmar sin declaración, con vacío yconusado.
2. Confirmar con declaración y código nuevo.
3. Leer stock, venta, constancia y efectivo.

**Resultados esperados:** Rechazos no mutan. Válido registra Yape 20/código, descuenta 2 stock y genera una constancia; caja en efectivo permanece 100. Texto explica comprobación manual externa, no promete validación bancaria automática ni acepta captura como prueba automática.

<a id="EPIC-REP"></a>

## EPIC-REP · Control del negocio

<a id="HU-CONF-01"></a>

### HU-CONF-01 · Configuración — Ver configuración actual del negocio

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 1 (orientativos; anteriores:1).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero ver los datos de la bodega configurados en el sistema (nombre comercial, RUC, dirección, teléfono y logotipo propio), para comprobar que la información sea correcta.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-AUTH-01.

**Orden de producto:** 44.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CONF-01-CA-01"></a>

**HU-CONF-01/CA-01.** Dado que accedo a la sección de configuración, cuando la pantalla carga, entonces veo el nombre del minimarket, RUC, dirección, teléfono y logotipo propio que se usan en la constancia interna.

<a id="HU-CONF-01-CA-02"></a>

**HU-CONF-01/CA-02.** Dado que faltan datos por registrar, cuando consulto la configuración, entonces el sistema señala con una advertencia visual los datos incompletos.

#### Casos de prueba escritos

<a id="CP-HU-CONF-01-001"></a>
##### CP-HU-CONF-01-001 · Configuración futura y faltantes

**Cubre:** HU-CONF-01/CA-01, HU-CONF-01/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; nombre Minimarket Prueba, RUC ficticio 20123456789, dirección CallePrueba123, teléfono vacío, logo ausente.

1. Abrir configuración.
2. Comparar encabezado de constancia y advertencias.

**Resultados esperados:** Campos guardados visibles; teléfono/logo ausentes señala dos sin inventar los. Datos ficticios no son identidad real ni validación SUNAT.

<a id="HU-CONF-02"></a>

### HU-CONF-02 · Configuración — Actualizar configuración del negocio

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador, quiero actualizar el nombre del minimarket, RUC, dirección, teléfono y logotipo propio, para que las constancias internas reflejen la información vigente.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-CONF-01.

**Orden de producto:** 45.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-CONF-02-CA-01"></a>

**HU-CONF-02/CA-01.** Dado que actualizo el nombre comercial, RUC, dirección o teléfono y guardo, cuando se genera una nueva constancia interna de venta, entonces los datos actualizados aparecen en el encabezado.

<a id="HU-CONF-02-CA-02"></a>

**HU-CONF-02/CA-02.** Dado que cargo una imagen con el logotipo propio de la bodega, cuando guardo, entonces el logo se muestra en la constancia interna y en la pantalla principal.

<a id="HU-CONF-02-CA-03"></a>

**HU-CONF-02/CA-03.** Dado que el sistema emite únicamente constancias internas sin validez tributaria, cuando guardo la configuración, entonces no se definen series de facturas ni boletas oficiales.

#### Casos de prueba escritos

<a id="CP-HU-CONF-02-001"></a>
##### CP-HU-CONF-02-001 · Cambiar configuración sin reescribir historia

**Cubre:** HU-CONF-02/CA-01, HU-CONF-02/CA-02, HU-CONF-02/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; constancia vieja Minimarket Prueba; nuevo nombre Tienda Prueba, logo ficticio PNG válido; archivo SVG con script en variante de rechazo.

1. Actualizar nombre/dirección/logo y guardar.
2. Generar nueva constancia; reabrir antigua.
3. Intentar series fiscales y archivo peligroso.

**Resultados esperados:** Nueva constancia y pantalla principal usan configuración nueva; histórica mantiene snapshot. No crea series boleta/factura; archivo peligroso rechazado de forma control a da. Límites de archivo/formato seprecisan antes de seleccionar la HU.

<a id="HU-DASH-01"></a>

### HU-DASH-01 · Resumen del negocio — Ver indicadores de ventas en tiempo real

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero ver en el resumen del negocio los indicadores comerciales del día (ventas totales, cantidad de operaciones y ticket promedio), para seguir el movimiento de la bodega en tiempo real.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 54.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-DASH-01-CA-01"></a>

**HU-DASH-01/CA-01.** Dado que ingreso al resumen del negocio, cuando carga la pantalla, entonces muestra los indicadores del día: Ventas Totales en soles, Número de Ventas y Ticket Promedio.

<a id="HU-DASH-01-CA-02"></a>

**HU-DASH-01/CA-02.** Dado que se cobra una nueva venta en mostrador, cuando se confirma la operación, entonces los indicadores del día se recalculan y muestran las cifras actualizadas.

<a id="HU-DASH-01-CA-03"></a>

**HU-DASH-01/CA-03.** Dado que selecciono Hoy, Esta semana o Este mes, cuando aplico la opción, entonces los indicadores usan America/Lima desde el inicio de hoy, del lunes de esta semana o del primer día del mes respectivamente, hasta el instante de consulta, con el rango visible; no incluyen fechas posteriores a ese corte.

#### Casos de prueba escritos

<a id="CP-HU-DASH-01-001"></a>
##### CP-HU-DASH-01-001 · Indicadores futuros por período

**Cubre:** HU-DASH-01/CA-01, HU-DASH-01/CA-02, HU-DASH-01/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; F-VENTAS:12/11 ventas 20+30; 11/11 venta 10; 13/11 venta 40 fuera del hoy; nueva venta 10 hoy.

1. Consultar Hoy.
2. Registrar venta 10 y comprobar la actualización de indicadores.
3. Consultar semana/mes que incluye 11 y 12 sin incluir futuro 13.

**Resultados esperados:** Inicial hoy total 50, cantidad 2, ticket 25; tras nueva venta 60,3,20. Semana/mes hasta ahora 70,4,17.50 según rango visible. Cifras etiquetan corte/actualización; la promesa de actualización requiere observación en navegador y una latencia máxima definida al refinar esta función futura; no se declara verificada por calcular bien los agregados.

<a id="HU-DASH-02"></a>

### HU-DASH-02 · Resumen del negocio — Ver gráfico de evolución de ventas por día

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero ver un gráfico con la evolución diaria de ventas en el período seleccionado, para evaluar las altas y bajas en las ventas del minimarket.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 61.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-DASH-02-CA-01"></a>

**HU-DASH-02/CA-01.** Dado que accedo al resumen del negocio y existen ventas en el período, cuando el gráfico carga, entonces muestra el monto vendido por cada día del lapso elegido.

<a id="HU-DASH-02-CA-02"></a>

**HU-DASH-02/CA-02.** Dado que en un día determinado no hubo ventas, cuando se grafica, entonces dicho día se representa con valor cero sin errores.

#### Casos de prueba escritos

<a id="CP-HU-DASH-02-001"></a>
##### CP-HU-DASH-02-001 · Gráfico futuro incluye día sin venta

**Cubre:** HU-DASH-02/CA-01, HU-DASH-02/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; rango 10..12 nov:10 sin venta,11 total 10,12 total 50.

1. Aplicar rango y comparar puntos/tabla de valores.

**Resultados esperados:** Tres días Lima:0,10,50. Ejes/etiquetas coinciden; no omite 10 ni reparte por UTC. Consulta no cambia operaciones.

<a id="HU-DASH-03"></a>

### HU-DASH-03 · Resumen del negocio – Ver alertas operativas (stock crítico, vencimientos y turnos)

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero ver en el resumen del negocio las alertas de productos con existencias mínimas, lotes por vencer y turnos sin actividad, para tomar decisiones oportunas.

**Reglas relacionadas:** RN-06, RN-23. **Dependencias funcionales:** HU-INV-01a, HU-CAJA-05 y HU-PROD-06.

**Orden de producto:** 53.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DEC-07-VENCIDOS-FILTRO](#contrato-DEC-07-VENCIDOS-FILTRO).

#### Criterios de aceptación

<a id="HU-DASH-03-CA-01"></a>

**HU-DASH-03/CA-01.** Dado que uno o más productos se encuentran en o por debajo de su cantidad mínima (10 unidades por defecto según RN-06), cuando abro el resumen, entonces muestra la alerta de existencias críticas indicando el producto y las unidades disponibles.

<a id="HU-DASH-03-CA-02"></a>

**HU-DASH-03/CA-02.** Dado que existen lotes de mercadería cuya caducidad se cumplirá en los próximos 7 días, cuando consulto las alertas, entonces el sistema advierte el vencimiento inminente con el lote y los días restantes.

<a id="HU-DASH-03-CA-03"></a>

**HU-DASH-03/CA-03.** Dado que un turno de caja permanece abierto sin operaciones durante 2 horas consecutivas o más (RN-23), cuando el sistema revisa los turnos, entonces muestra la alerta informativa de turno inactivo u olvidado.

#### Casos de prueba escritos

<a id="CP-HU-DASH-03-001"></a>
##### CP-HU-DASH-03-001 · Alertas futuras y ventanas explícitas

**Cubre:** HU-DASH-03/CA-01, HU-DASH-03/CA-02, HU-DASH-03/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; Arroz 5 mínimo 10; lote A vence 13 nov, lote B12 dic; reloj 12 nov 12:00; turno última operación 10:00.

1. Abrir alertas 7 días y revisar stock crítico/turno.
2. Comparar con panel mínimo actual 30 días.

**Resultados esperados:** Stock crítico Arroz 5; ventana 7 días incluye Ayno B; turno 2 h informativo. Panel actual 30 puede incluir B con etiqueta 30; no conf und ir ventanas ni declarar todo DASH implementado.

<a id="HU-DASH-04"></a>

### HU-DASH-04 · Resumen del negocio – Ver ranking de productos más vendidos

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero ver en el resumen del negocio un recuadro informativo con los 5 productos más vendidos del período, para reconocer los artículos con mayor rotación en mostrador.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 62.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-DASH-04-CA-01"></a>

**HU-DASH-04/CA-01.** Dado que accedo al resumen del negocio, cuando carga el recuadro informativo, entonces muestra los 5 productos con mayor cantidad de unidades vendidas en el período.

<a id="HU-DASH-04-CA-02"></a>

**HU-DASH-04/CA-02.** Dado que no existen ventas registradas en dicho período, cuando carga el recuadro, entonces informa «Sin ventas registradas en este período».

#### Casos de prueba escritos

<a id="CP-HU-DASH-04-001"></a>
##### CP-HU-DASH-04-001 · Top 5 futuro y vacío

**Cubre:** HU-DASH-04/CA-01, HU-DASH-04/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; seis productos con unidades 10,8,6,4,2,1 en período; variante sin ventas.

1. Abrirtop 5.
2. Cambiar a período sin ventas.

**Resultados esperados:** Cinco productos 10,8,6,4,2 en orden; empates resueltos con orden determinista. Vacío Sin ventas registradas en este período.

<a id="HU-DASH-05"></a>

### HU-DASH-05 · Resumen del negocio — Ver solicitudes de reposición pendientes

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero ver en el resumen del negocio la lista de solicitudes de reposición pendientes de revisión, para atender las compras sin demoras.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-SOL-01.

**Orden de producto:** 63.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-DASH-05-CA-01"></a>

**HU-DASH-05/CA-01.** Dado que existen solicitudes en estado Pendiente, cuando abro el resumen, entonces el recuadro muestra el producto sugerido, la cantidad, el empleado solicitante y la fecha.

<a id="HU-DASH-05-CA-02"></a>

**HU-DASH-05/CA-02.** Dado que selecciono una solicitud en el recuadro, cuando hago clic, entonces me conduce a la pantalla para aprobar o rechazar dicha solicitud.

<a id="HU-DASH-05-CA-03"></a>

**HU-DASH-05/CA-03.** Dado que no existen solicitudes pendientes, cuando abro la pantalla, entonces informa «Sin solicitudes pendientes».

#### Casos de prueba escritos

<a id="CP-HU-DASH-05-001"></a>
##### CP-HU-DASH-05-001 · Pendientes futuros y navegación

**Cubre:** HU-DASH-05/CA-01, HU-DASH-05/CA-02, HU-DASH-05/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; S1Pendiente Arroz 12 solicitante ALMACENERO12 nov; S2Aprobada.

1. Abrir panel y seleccionar S1.
2. Resolver S1 y recargar panel.

**Resultados esperados:** Solo S1 con producto/cantidad/empleado/fecha; enlaza a detalle autorizado para aprobar/rechazar. Resuelta la última: Sin solicitudes pendientes; no ingresa stock por abrir enlace.

<a id="HU-REP-01"></a>

### HU-REP-01 · Reportes — Consultar reporte analítico de ventas totales por período

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero consultar un reporte detallado de ventas con filtros por fecha y medio de pago, para analizar los ingresos de la bodega.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 55.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-01-CA-01"></a>

**HU-REP-01/CA-01.** Dado que ingreso al reporte analítico de ventas, cuando selecciono un rango de fechas, entonces el sistema lista las ventas con fecha, número interno, medio de pago, base imponible, IGV y total.

<a id="HU-REP-01-CA-02"></a>

**HU-REP-01/CA-02.** Dado que aplico el filtro por medio de pago (efectivo o Yape digital), cuando consulto, entonces muestra únicamente las operaciones cobradas por dicho canal y su suma acumulada.

#### Casos de prueba escritos

<a id="CP-HU-REP-01-001"></a>
##### CP-HU-REP-01-001 · Reporte futuro de ventas y filtros

**Cubre:** HU-REP-01/CA-01, HU-REP-01/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; 12 nov venta efectivo 20 base 16.95IGV3.05 y Yape 30 base 25.42IGV4.58; 11 nov efectivo 10.

1. Consultar 12 nov todos medios.
2. Filtrar efectivo y luego Yape.

**Resultados esperados:** Todos 2 filas total 50, base 42.37, IGV7.63 con fecha/número/medio. Efectivo solo 20, Yape solo 30; no incluye 11 nov. Importes provienen de snapshots; rango/permisos valida dos.

<a id="HU-REP-02"></a>

### HU-REP-02 · Reportes – Consultar reporte completo de ranking de productos más vendidos

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño de la bodega, quiero consultar el ranking completo de productos vendidos y su porcentaje de participación, para identificar los artículos más demandados y planificar compras.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 56.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-02-CA-01"></a>

**HU-REP-02/CA-01.** Dado que consulto el reporte de ranking en un rango de fechas, cuando se generan los resultados, entonces ordena los productos de mayor a menor según las unidades vendidas y el importe total cobrado.

<a id="HU-REP-02-CA-02"></a>

**HU-REP-02/CA-02.** Dado que se calcula la participación sobre las ventas del período, cuando reviso cada fila, entonces muestra el porcentaje de participación de cada producto sobre el total vendido.

<a id="HU-REP-02-CA-03"></a>

**HU-REP-02/CA-03.** Dado que deseo ordenar la tabla, cuando hago clic en los encabezados, entonces permite ordenar por unidades vendidas o por monto total.

#### Casos de prueba escritos

<a id="CP-HU-REP-02-001"></a>
##### CP-HU-REP-02-001 · Ranking futuro y participación

**Cubre:** HU-REP-02/CA-01, HU-REP-02/CA-02, HU-REP-02/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; Leche 3 unidades importe 30, Arroz 4 importe 20 en período, total 50.

1. Ordenar por unidades y después por monto.
2. Revisar porcentajes.

**Resultados esperados:** Unidades:Arroz 4 antes Leche 3; monto:Leche 30 antes Arroz 20. Participación monetaria 60%Leche/40%Arroz, suma 100%; denominador visible. Totales calcula dos en conjunto filtrado.

<a id="HU-REP-03"></a>

### HU-REP-03 · Reportes — Ver ventas desglosadas por día

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero consultar las ventas detalladas día por día dentro de un período, para conocer los días de mayor movimiento en la tienda.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c.

**Orden de producto:** 64.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-03-CA-01"></a>

**HU-REP-03/CA-01.** Dado que accedo al reporte de ventas por día, cuando el informe carga, entonces veo una fila por cada día del período con el total de dinero vendido y la cantidad de operaciones.

<a id="HU-REP-03-CA-02"></a>

**HU-REP-03/CA-02.** Dado que un día del rango no registró ventas, cuando aparece en el reporte, entonces muestra cero sin omitir el día de la lista.

#### Casos de prueba escritos

<a id="CP-HU-REP-03-001"></a>
##### CP-HU-REP-03-001 · Detalle diario futuro continuo

**Cubre:** HU-REP-03/CA-01, HU-REP-03/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; 10 nov 0 ventas,11 nov 1×10,12 nov 20+30.

1. Consultar 10..12 nov y sumar filas.

**Resultados esperados:** Filas 10 nov:0/0; 11 nov:10/1; 12 nov:50/2; total 60/3. Fecha de negocio Lima; días sin operación no se ocultan.

<a id="HU-REP-04"></a>

### HU-REP-04 · Reportes — Ver ventas por método de pago

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero consultar el desglose de ventas según el medio de cobro (efectivo o digital), para conciliar los ingresos y vigilar el efectivo disponible.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-VEN-01c y HU-VEN-07.

**Orden de producto:** 57.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-04-CA-01"></a>

**HU-REP-04/CA-01.** Dado que accedo al reporte de medios de pago, cuando carga el informe, entonces veo el total recaudado en efectivo y el total recaudado por Yape en el período.

<a id="HU-REP-04-CA-02"></a>

**HU-REP-04/CA-02.** Dado que aplico un filtro de fechas, cuando el informe se actualiza, entonces los montos reflejan exclusivamente las ventas del rango elegido.

#### Casos de prueba escritos

<a id="CP-HU-REP-04-001"></a>
##### CP-HU-REP-04-001 · Medios futuros separados del efectivo en caja

**Cubre:** HU-REP-04/CA-01, HU-REP-04/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; 12 nov efectivo 20/Yape 30; 11 nov efectivo 10.

1. Consultar 12 nov y luego rango 11..12.

**Resultados esperados:** 12 nov efectivo 20 digital 30; rango efectivo 30 digital 30. Total ventas distingue dinero en gaveta yno incluye apertura como venta.

<a id="HU-REP-05"></a>

### HU-REP-05 · Reportes – Consultar reporte de productos bajo stock mínimo

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como administrador o dueño, quiero consultar un reporte de los productos que están en o por debajo de su cantidad mínima configurada, para coordinar los pedidos de mercadería a tiempo.

**Reglas relacionadas:** RN-06. **Dependencias funcionales:** HU-INV-01a.

**Orden de producto:** 52.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-05-CA-01"></a>

**HU-REP-05/CA-01.** Dado que accedo al reporte de existencias críticas, cuando el sistema lo genera, entonces lista todos los artículos cuyo stock disponible actual es menor o igual al umbral mínimo configurado (10 unidades por defecto según RN-06).

<a id="HU-REP-05-CA-02"></a>

**HU-REP-05/CA-02.** Dado que visualizo la lista, cuando consulto cada artículo, entonces muestra existencias actuales, cantidad mínima, categoría y unidad de medida.

<a id="HU-REP-05-CA-03"></a>

**HU-REP-05/CA-03.** Dado que un producto tiene existencias en cero, cuando aparece en la lista, entonces se resalta con el estado «Agotado» para priorizar su reposición.

#### Casos de prueba escritos

<a id="CP-HU-REP-05-001"></a>
##### CP-HU-REP-05-001 · Crítico futuro según disponibilidad

**Cubre:** HU-REP-05/CA-01, HU-REP-05/CA-02, HU-REP-05/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; Arroz 5 mínimo 10, Leche 20 mínimo 10, Yogur 0 mínimo 0, producto inactivo 0 mínimo 10.

1. Abrir reporte y ver columnas/estados.

**Resultados esperados:** Arroz 5 y Yogur 0 incluidos por<=mínimo; Yogur Agotado. Leche no; inactivo no dispara reposición. Nombre, stock vendible, mínimo, categoría, UN Dvisibles.

<a id="HU-REP-06"></a>

### HU-REP-06 · Reportes — Ver resumen general del inventario

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 2 (orientativos; anteriores:2).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero consultar el resumen de existencias de todos los productos, para tener visibilidad completa del almacén sin realizar un conteo físico completo.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-INV-01a.

**Orden de producto:** 58.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-06-CA-01"></a>

**HU-REP-06/CA-01.** Dado que abro el resumen de existencias, cuando el informe carga, entonces veo todos los productos con su stock actual, cantidad mínima y una indicación de estado normal o crítico.

<a id="HU-REP-06-CA-02"></a>

**HU-REP-06/CA-02.** Dado que busco un producto por nombre, cuando el sistema filtra, entonces muestra solo los productos coincidentes.

#### Casos de prueba escritos

<a id="CP-HU-REP-06-001"></a>
##### CP-HU-REP-06-001 · Inventario futuro separa físico y vendible

**Cubre:** HU-REP-06/CA-01, HU-REP-06/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; Leche 18 físico/10 vendible, mínimo 10; Arroz 5/5 mínimo 10; producto inactivo 2 físico.

1. Abrir resumen y buscar Leche.

**Resultados esperados:** Todos productos identifica dos con estado; stock etiqueta físico y vendible sin conf und ir 18 con 10. Leche crítico por 10<=10; filtro solo Leche. No afirma que la consulta equivalga a conteo físico.

<a id="HU-REP-07"></a>

### HU-REP-07 · Reportes — Ver margen de ganancia por producto

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 5 (orientativos; anteriores:5).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño de la bodega, quiero consultar el margen comercial de las ventas con costo histórico conocido y base comparable documentada, para analizar la mercadería sin confundir esa medida con la rentabilidad neta del negocio.

**Reglas relacionadas:** RN-14, RN-27, RN-28. **Dependencias funcionales:** HU-VEN-01c y HU-INV-01a.

**Orden de producto:** 59.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** [DOC-03AH-01](#contrato-DOC-03AH-01), [DEC-11-MODELO-AUDITORIA-VENTAS](#contrato-DEC-11-MODELO-AUDITORIA-VENTAS).

#### Criterios de aceptación

<a id="HU-REP-07-CA-01"></a>

**HU-REP-07/CA-01.** Dado un conjunto de ventas con precio neto sin IGV y costo histórico cuya base comparable está documentada, cuando ADMIN consulta el reporte, entonces presenta ingresos netos, costo conservado y ganancia comercial; si falta costo o su base comparable, identifica la exclusión y no calcula una ganancia ficticia (RN-27, RN-28).

<a id="HU-REP-07-CA-02"></a>

**HU-REP-07/CA-02.** Dado un conjunto con datos comparables conocidos, cuando se calcula el margen, entonces muestra ganancia/ingreso neto ×100, con denominador y cobertura explícitos; si el ingreso neto es cero o faltan datos, indica No calculable, sin presentar el resultado como rentabilidad neta ni certificación fiscal.

<a id="HU-REP-07-CA-03"></a>

**HU-REP-07/CA-03.** Dado que filtro por categoría o rango de fechas, cuando consulto, entonces el sistema lista los productos vendidos en ese lapso evaluando el margen porcentual y la ganancia total obtenida.

#### Casos de prueba escritos

<a id="CP-HU-REP-07-001"></a>
##### CP-HU-REP-07-001 · Margen futuro con cobertura de costo

**Cubre:** HU-REP-07/CA-01, HU-REP-07/CA-02, HU-REP-07/CA-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; fixture sintético con base comparable documentada: venta 1 producto 11.80, neto 10, costo histórico 6 sin IGV recuperable; otra venta costo desconocido; filtro Lácteos 12 nov.

1. Aplicar filtro y consultar margen.
2. Cambiar costo maestro a 8 y repetir.
3. Retirar evidencia de base comparable del costo.

**Resultados esperados:** Con base comparable documentada: ganancia 4 y margen 40% del neto; no cambia por costo maestro 8. Costo desconocido excluido del margen y cobertura expuesta, sin convertir NULL a 0. Sin base comparable el informe indica margen no calculable; no promete rentabilidad neta ni certificación fiscal. La definición de base del costo es dependencia antes de implementación.

<a id="HU-REP-08"></a>

### HU-REP-08 · Reportes — Ver mermas agrupadas por motivo

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero consultar el informe de bajas de mercadería agrupadas por motivo, para cuantificar las pérdidas y tomar acciones preventivas.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-INV-02.

**Orden de producto:** 60.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-08-CA-01"></a>

**HU-REP-08/CA-01.** Dado que accedo al reporte de mermas, cuando el informe carga, entonces veo las unidades dadas de baja agrupadas por causa reconocida (Vencimiento, Daño o rotura, y Robo o faltante) en el período seleccionado.

<a id="HU-REP-08-CA-02"></a>

**HU-REP-08/CA-02.** Dado que aplico un filtro de fechas, cuando el informe se actualiza, entonces presenta únicamente las bajas registradas en ese rango.

#### Casos de prueba escritos

<a id="CP-HU-REP-08-001"></a>
##### CP-HU-REP-08-001 · Mermas futuras agrupadas

**Cubre:** HU-REP-08/CA-01, HU-REP-08/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; 12 nov vencimiento 2, daño 1, robo 3; 11 nov daño 4.

1. Consultar 12 nov y luego rango 11..12.

**Resultados esperados:** 12 nov, agrupaciones 2/1/3, total 6; rango 2/5/3, total 10. Responsabilidad/lote permanece en origen; no agrupar robo de lote vencido como vencimiento por fecha.

<a id="HU-REP-09"></a>

### HU-REP-09 · Reportes — Exportar reportes analíticos de gestión a PDF

**Épica:** EPIC-REP. **Prioridad MoSCoW:** W. **Puntos Fibonacci:** 3 (orientativos; anteriores:3).

**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.

**Descripción de la HU:** Como dueño o administrador, quiero descargar en archivo PDF los reportes analíticos de gestión, para compartir información con el contador o archivarla físicamente.

**Reglas relacionadas:** —. **Dependencias funcionales:** HU-REP-01, HU-REP-02, HU-REP-05, HU-REP-07 y HU-REP-08.

**Orden de producto:** 65.

**Estimación:** Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.

**Procedencia:** ETAPA-13; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md).

**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.

#### Criterios de aceptación

<a id="HU-REP-09-CA-01"></a>

**HU-REP-09/CA-01.** Dado que visualizo un reporte analítico de gestión en pantalla, cuando elijo la opción de exportar a PDF, entonces el sistema genera y descarga un archivo PDF con los datos y filtros consultados.

<a id="HU-REP-09-CA-02"></a>

**HU-REP-09/CA-02.** Dado que el reporte no contiene información en el período seleccionado, cuando intento descargarlo, entonces el archivo PDF se genera indicando que no hay datos registrados sin provocar errores.

#### Casos de prueba escritos

<a id="CP-HU-REP-09-001"></a>
##### CP-HU-REP-09-001 · PDF futuro conserva filtros y vacío

**Cubre:** HU-REP-09/CA-01, HU-REP-09/CA-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Datos ficticios aislados; restaurar F-BASE antes del caso. Rol indicado autenticado salvo prueba de ingreso.
**Datos de prueba:** FUTURO; ADMIN; reporte 12 nov efectivo 20; variante período sin registros.

1. Exportar reporte filtrado a PDF y abrir archivo.
2. Repetir con reporte vacío; solicitar descarga como VENDEDOR.

**Resultados esperados:** PDF legible identifica reporte/rango/medio/corte y contiene solo 20 igual a pantalla, sin truncar columnas/páginas. Vacío genera Sin datos registrados. Permisos idénticos a pantalla; no filtrar datos global es por el endpoint de descarga.

<a id="reglas"></a>

## Anexo normativo · Reglas de negocio

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

<a id="contratos"></a>

## Anexo normativo · Decisiones y encargos implementables

### Condiciones comunes

- Confirmar rol activo y permiso en servidor; validar nuevamente dentro de la transacción los actores/entidades que compiten. Un menú oculto no autoriza una petición. Visitante no es un cuarto rol.
- Entradas inválidas, estado omitido, UUID ajeno, CSRF inválido, usuario revocado, doble envío divergente y límites excedidos deben producir un error comprensible sin efectos parciales en stock, costo, lotes, venta, correlativo, turno ni efectivo. Verificar el conjunto completo de datos antes/después; un HTTP400/403 no basta.
- Las escrituras se hacen por POST. GET es consulta. Usar orden de locks común, documentado a partir de todos los servicios implicados, y pruebas de carrera real en PostgreSQL con conexiones independientes/barrera que demuestre solapamiento. Registrar cuándo se usa Django Client, HTTP por sockets o navegador real; no intercambiar esos nombres.
- Registrar migración/diagnóstico de datos, reversibilidad y backup/restauración en un clon. Nunca fusionar, borrar, completar ni revalorar datos operativos por inferencia. Costos históricos desconocidos quedan desconocidos y los reportes indican cobertura.
- Actualizar HU/RN afectadas, este registro, backlog, matriz y evidencia en la misma entrega. Verificación: unitarias de cálculo/forma, integración de transacción, permisos, concurrencia cuando hay recursos compartidos, navegador para comportamiento visible y regresión integral. La DoD exige el alcance completo acordado, no solo tests verdes.
- Mensajes específicos pueden adaptar el estilo visual, pero deben comunicar causa y siguiente acción sin revelar secretos. Nunca guardar contraseñas, cookies, CSRF, tokens ni cuerpos completos sensibles en logs. Datos de prueba ficticios, base nueva y hashes del producto/base operativa antes y después.

Cada contrato conserva ID, justificación, alcance/excepciones, dependencias, requisitos, migración y criterios verificables. Estado de decisión: ACEPTADA por delegación12/11; implementación de cambios PENDIENTE DE AUTORIZACIÓN SEPARADA; verificación de esos cambios NO EJECUTADA. CT-ROLLBACK es investigación/prueba pendiente, no defecto demostrado.

<a id="contrato-DOC-03AB-01"></a>

### DOC-03AB-01 · Entrada directa de almacén

**Decisión/justificación.** Mantener la recepción ordinaria directa por ALMACENERO, para no imponer un circuito SOL completo al minimarket. ADMIN autoriza compras mediante el procedimiento externo del negocio; el sistema registra recepción, no acredita aprobación externa. Esta política tiene costo relativo bajo-medio; SOL completo queda futuro. Cambiaría si la operación real requiere autorización previa trazable por importe o comprador.

**Alcance.** RN-01, HU-INV-01b, HU-SOL-01..05b, backlog/diseño/matriz. Producto y categoría activos; carga inicial confirmada; proveedor activo opcional, con etiqueta «Sin proveedor asignado» si falta. No suponer RUC ni proveedor inexistentes. Si el negocio adopta proveedor obligatorio se necesita cambio posterior explícito, no una falsa obligación fiscal.

<a id="DOC-03AB-01-C-01"></a>

**DOC-03AB-01/C-01.** Dado un producto habilitado y su carga inicial, cuando ALMACENERO confirma una recepción válida, entonces se registra con identidad propia, autor, instante Lima/UTC, lotes, cantidades y costos, sin exigir solicitud SOL.

<a id="DOC-03AB-01-C-02"></a>

**DOC-03AB-01/C-02.** Dada una solicitud inexistente o futura, cuando se consulta la recepción actual, entonces no se presenta como «solicitud aprobada». ADMIN/VENDEDOR no reciben permiso de escritura de almacén por conocer la URL.

**Migración/excepciones.** Ningún cambio de stock por documentar la excepción. Recepciones antiguas conservan origen conocido; no fabricar aprobaciones. Depende de DOC-03AI-01/03AH-01 antes de considerar completa la recepción.

<a id="CP-DOC-03AB-01-001"></a>
##### CP-DOC-03AB-01-001 · Contrato DOC-03AB-01

**Cubre:** DOC-03AB-01/C-01, DOC-03AB-01/C-02. **Estado:** EJECUTADO PARCIAL en muestra aislada (ETAPA-06, 14/11/2026): C-01 y C-02 comprobados en servidor HTTP/CSRF y Chrome (`ALMACENERO` confirma sin `SOL` y con `Sin proveedor asignado`, `ADMIN` solo lectura/`403` entrada, `VENDEDOR` `403`, anónimo `302`) más verificación de `0` rutas/plantillas `HU-SOL-*`; base operativa y revisión global Etapas 15/17 pendientes. [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114).
**Evidencia de ejecución:** [ETAPA-06 servidor](auditoria_por_etapas/resultados/evidencias/06-reval-server-20261114T212733200909Z-caa926fa/report.json), [ETAPA-06 Chrome](auditoria_por_etapas/resultados/evidencias/06-reval-browser-20261114T212745468050Z-dce3e1b1/browser.json).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** ALMACENERO; Leche con carga confirmada; lote C, 10 unidades a S/6, vence 12/12/2026; sin SOL y sin proveedor. Repetir como ADMIN y VENDEDOR.

1. Confirmar la recepción directa.
2. Consultar referencia, autor, fecha, lotes y origen.
3. Restaurar y enviar la misma petición con cada rol denegado.

**Resultados esperados:** Recepción propia con origen directo y «Sin proveedor asignado»; no afirma autorización externa o solicitud aprobada. ADMIN/VENDEDOR no crean recepción, lotes, stock, promedio ni correlativo.

<a id="contrato-DOC-03AH-01"></a>

### DOC-03AH-01 · Promedio móvil coherente

**Decisión.** Promedio ponderado sobre existencia física registrada, incluyendo vencidos pendientes de baja. Venta/baja/ajuste negativo conserva costo unitario promedio; al quedar stock físico total cero, promedio vigente=0. Expirar no modifica stock físico ni promedio: impide venta. Esto separa disponibilidad y valoración interna. No constituye método fiscal certificado ni valoración al menor entre costo y valor realizable.

**Entradas y cálculo.** Decimales, precisión4, HALF_UP. Entrada: `(Q×C + q×c)/(Q+q)`, con Q físico y C promedio anterior bloqueados; carga inicial pondera todas sus líneas. Ajuste positivo por conteo con Q>0 usa el promedio vigente para las unidades encontradas, no inventa compra; con Q=0 exige costo positivo documentado y fuente/motivo explícitos. Si falta costo fiable se rechaza y se requiere investigar, sin permitir venta de existencia no regularizada. Una recepción real usa su costo de adquisición declarado, no el costo del ajuste.

<a id="DOC-03AH-01-C-01"></a>

**DOC-03AH-01/C-01.** Dadas18 unidades registradas con promedio 3 (8 vencidas,10 vendibles), cuando llegan10 a6, entonces Q=28, vendible 20 y C=4.0714. La fecha de vencimiento sola no altera C.

<a id="DOC-03AH-01-C-02"></a>

**DOC-03AH-01/C-02.** Dado stock con promedio 4.0714, cuando se vende/dá de baja una unidad, entonces la salida conserva ese costo histórico y C sigue4.0714 si queda stock; si queda cero, C=0 sin alterar snapshots previos.

<a id="DOC-03AH-01-C-03"></a>

**DOC-03AH-01/C-03.** Dado un ajuste positivo con Q>0, cuando se confirma, entonces aumenta Q al promedio vigente y conserva su procedencia como ajuste. Con Q=0 y costo ausente, rechaza sin mutación.

<a id="DOC-03AH-01-C-04"></a>

**DOC-03AH-01/C-04.** Dadas recepción y venta/baja concurrentes, cuando se solapan, entonces cada resultado equivale a uno de los órdenes seriales válidos; ninguna pierde cantidades ni usa un promedio a medio actualizar. Con fallo posterior a escritura, rollback total.

**Datos.** Diagnosticar historia y corte de valoración antes de cambiar algoritmo. No retrocalcular `SaleLine.unit_cost=NULL` con promedio actual ni reescribir ventas conocidas. Si no hay historia suficiente, preparar ajuste de apertura de valoración explícito, documentado y autorizado antes de aplicarlo. Afecta RN-14/28, INV01a/01b/02/03, VEN01c y REP07 futuro. La prueba antigua que exige recalcular por costos de lotes restantes se sustituye con trazabilidad; no se elimina simplemente para obtener verde.

**Representación adoptada14-E.** `StockWriteOff.unit_cost` y `PhysicalAdjustment.unit_cost` capturan el promedio bloqueado previo a la salida o ajuste, con Decimal4. Migración aditiva nullable, sin valor predeterminado ni reconstrucción: costos de operaciones anteriores permanecenNULL/desconocidos. El promedio vigente puede pasar a0 sin alterar esos registros ni `SaleLine.unit_cost`. Se mantiene el contrato de no inventar historia. Esta concreción técnica se acepta dentro de la corrección autorizada de RN-14/28; no sustituye constancias ni asignaciones de lote. [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-E-disposiciones.md).

<a id="CP-DOC-03AH-01-001"></a>
##### CP-DOC-03AH-01-001 · Contrato DOC-03AH-01

**Cubre:** DOC-03AH-01/C-01, DOC-03AH-01/C-02, DOC-03AH-01/C-03, DOC-03AH-01/C-04. **Estado:** EJECUTADO PARCIAL (14-E 13/11/2026 + revalidación ETAPA-06 14/11/2026): C-01..03 revalidados en F-COSTO (`18@3`→`28@4.0714`→`33@4.6666`→`0.0000` al agotar); C-04 ampliado con carreras reales PostgreSQL `18.4` (`register_stock_entry` vs `checkout_sale` serializable con espera `Lock/transactionid` en `pg_blocking_pids`, carrera 3 vías entrada/merma/ajuste y rollback pos-escritura + trigger `23514`). Nota: la captura documentada Q0 se implementó posteriormente en `14-CIERRE` (ETAPA-06 solo verificó rechazo Q0 sin costo). `PG 17` objetivo, caída real `SIGKILL` y diagnóstico/migración operativa siguen pendientes. [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114) · [Informe 14-E](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e).
**Evidencia de ejecución:** [ETAPA-06 servidor](auditoria_por_etapas/resultados/evidencias/06-reval-server-20261114T212733200909Z-caa926fa/report.json), [ETAPA-06 Chrome](auditoria_por_etapas/resultados/evidencias/06-reval-browser-20261114T212745468050Z-dce3e1b1/browser.json), [ETAPA-06 PG 18.4](auditoria_por_etapas/resultados/evidencias/06-reval-pg18-20261114T213329260785Z.json), [23 casos 14-E servidor](auditoria_por_etapas/resultados/evidencias/14-E-20261113/servidor/costos-despues.json), [23 checkpoints 14-E Chrome](auditoria_por_etapas/resultados/evidencias/14-E-20261113/navegador/final/ejecucion.json), [migración 14-E](auditoria_por_etapas/resultados/evidencias/14-E-20261113/servidor/INFORME.md). No se diagnosticó ni migró una base operativa.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** F-COSTO: físico 18, promedio 3; 8 vencidas y 10 vigentes. Entrada10 a6. Salida1. Ajuste+2. Variante físico 0 sin costo. Dos conexiones PostgreSQL independientes.

1. Recibir10; retirar1; ajustar+2.
2. Restaurar y probar ajuste positivo sin costo con físico 0.
3. Restaurar y solapar recepción/salida; inyectar fallo después de escribir la primera mutación.

**Resultados esperados:** Físico28/promedio 4.0714; salida deja27/promedio 4.0714 y snapshot4.0714; ajuste deja29/mismo promedio. Cero físico exige costo positivo documentado y rechaza si falta. Carrera equivale a un orden serial válido; fallo revierte todas las mutaciones. Costos históricos y NULL no se recalculan.

<a id="contrato-DOC-03AI-01"></a>

### DOC-03AI-01 · Recepción propia e idempotente

**Decisión.** Una recepción confirmada por producto y uno o varios lotes tiene UUID, referencia visible `R-00000001`, responsable, instante y contenido inmutable. El correlativo de recepción es global del minimarket, ascendente, único, de ocho dígitos, sin reinicio por producto/fecha/turno ni reutilización de números confirmados. Se reserva bajo lock dentro de la misma transacción; rollback no deja recepción parcial. Al agotarse99,999,999 se rechaza antes de mutar, con mensaje de capacidad y revisión administrativa, sin truncar o reiniciar. Carga inicial sigue siendo única y conserva su constancia. Recepción multiproducto y solicitudes se difieren. Costo medio: hay cambio de persistencia y migración.

**Modelo recomendado.** Identificar cada ingreso físico de lote por su recepción; conservar número comercial normalizado y vencimiento. Permitir que un mismo lote comercial llegue en recepciones distintas sin mezclar fecha/costo/proveedor/origen. Eliminar la unicidad global `(producto,número)` solamente al reemplazarla por integridad de recepción y comprobar colisiones. Dentro de una recepción, un mismo número/vencimiento no aparece duplicado: rechazar o consolidar antes de confirmar con vista explícita, nunca sumar silenciosamente en reintento. Para mismo número comercial con vencimiento contradictorio, rechazar hasta aclaración documentada. FEFO mantiene vencimiento→ingreso→ID inmutable. No imponer cinco tablas si una estructura menor preserva esas garantías.

<a id="DOC-03AI-01-C-01"></a>

**DOC-03AI-01/C-01.** Dada clave UUID nueva y entrada válida, cuando se confirma, entonces stock/costo/recepción/lotes/autor/correlativo se guardan en una transacción y se devuelve su constancia.

<a id="DOC-03AI-01-C-02"></a>

**DOC-03AI-01/C-02.** Dada una clave confirmada y el mismo actor/contenido, cuando se repite incluso tras perder la respuesta, entonces se devuelve exactamente la recepción anterior sin nuevos efectos. Distinto contenido/actor no obtiene datos ajenos y rechaza sin mutación. La huella usa valores normalizados, no el orden incidental del HTML.

<a id="DOC-03AI-01-C-03"></a>

**DOC-03AI-01/C-03.** Dado otro ingreso real del mismo lote comercial, cuando usa una clave nueva y datos coherentes, entonces se crea otra recepción conservando ambas procedencias. Dos conexiones con la misma clave producen una sola confirmación.

<a id="DOC-03AI-01-C-04"></a>

**DOC-03AI-01/C-04.** Dada una entrada inválida, cuando se corrige antes de confirmar, entonces no queda clave consumida como éxito ni lote/stock parcial. No confundir duplicado comercial con reintento técnico.

**Concreción técnica14-G, aceptada dentro de la delegación de integración.** Cabecera `StockReceipt` con UUID/clave única/huella canónica/referencia global y snapshots de producto, autor y proveedor; `StockReceiptLine` conserva cantidad/costo/vencimiento originales y vínculo único al lote físico; `StockReceiptCounter` reserva el correlativo dentro de la transacción. La huella ordena líneas normalizadas y usa costo a4decimales; no depende del orden de formularios. HTTP exige UUID y conserva la clave en errores. Las llamadas internas sin clave expresan un ingreso nuevo y generan UUID; un consumidor que necesite reintento debe conservar y reenviar la clave explícita. No se deduce idempotencia de un intervalo de tiempo ni de igualdad de lote.

La misma clave/actor/contenido recupera la recepción aunque producto/categoría/proveedor se hayan desactivado o haya vencido el lote, porque no confirma un ingreso nuevo; actor revocado continúa denegado. Clave ajena o contenido divergente se rechazan. La consulta ADMIN/ALMACENERO muestra referencia y fotografías originales; VENDEDOR no accede. Las selecciones de baja/ajuste y movimientos muestran referencia para distinguir entregas con igual número/vencimiento. El importe de cada línea se presenta a2decimales y su costo unitario a4; el promedio capturado tras ese ingreso se presenta a2 y no pretende ser el costo actual. [Fundamento y límites14-G](auditoria_por_etapas/resultados/soporte/14-G-disposiciones.md).

**Datos existentes.** La FK a `InitialInventoryLoad` no prueba que cada lote pertenezca a la primera carga. Migrar solo información demostrable; separar legado con origen incompleto y enlazar evidencias, sin inventar una factura, recepción multiproducto o correlación temporal. Cargas/entradas y snapshots conservan proveedor/autor originales aunque después se editen. RN01/14/19, INV01a/b/04, PROV01/04.

La cantidad recibida en una constancia es inmutable. Un ajuste positivo no modifica esa fotografía aunque el campo técnico actual `Lot.initial_quantity` aumente para admitir más saldo. Separar cantidad original recibida y movimientos posteriores; no usar una capacidad mutable como cantidad histórica de recepción.

**Concreción técnica14-H1, dependencia de Kardex.** Para cargas iniciales nuevas, cabecera nullable con nombre/código/unidad de producto, autor, proveedor/RUC o ausencia y promedio inicial; líneas tipadas `InitialLoadLine` con vínculo protegido a carga y lote, cantidad original, número, costo4decimales, vencimiento e instante de ingreso. Se captura dentro de la misma transacción y no se modifica por ajustes, entradas ni salidas. Se elige el patrón relacional ya usado por recepciones para validar cantidades y relaciones; no se requiere una tabla genérica de eventos ni JSON sin esquema. Sin backfill: valoresNULL y ausencia de líneas significan historia no disponible. La pantalla separa fotografía y existencias/promedio actuales; el legado no muestra capacidad mutable como cantidad original. Esta concreción realiza el requisito histórico ya aceptado, no agrega selección comercial ni autoriza datos operativos. [Fundamento14-H1](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).

<a id="CP-DOC-03AI-01-001"></a>
##### CP-DOC-03AI-01-001 · Contrato DOC-03AI-01

**Cubre:** DOC-03AI-01/C-01, DOC-03AI-01/C-02, DOC-03AI-01/C-03, DOC-03AI-01/C-04. **Estado:** EJECUTADO PARCIAL (14-G + revalidación ETAPA-06 14/11/2026): identidad, reenvío igual/divergente/actor, estados inactivos, corrección con clave conservada, recuperación Chrome tras `ERR_CONNECTION_RESET` por `/inventario/stock/`, tope `99999999`, rollback pos-escritura y concurrencia aislada PostgreSQL `18.4` (`PG06R-01..04, 08, 10` con 10 hilos y correlativos contiguos). Pendientes: `PG 17` objetivo, caída física real `SIGKILL`, Etapa 15 y base operativa. [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114) · [Evidencia 14-G](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g).
**Evidencia de ejecución:** [ETAPA-06 servidor](auditoria_por_etapas/resultados/evidencias/06-reval-server-20261114T212733200909Z-caa926fa/report.json), [ETAPA-06 Chrome](auditoria_por_etapas/resultados/evidencias/06-reval-browser-20261114T212745468050Z-dce3e1b1/browser.json), [ETAPA-06 PG 18.4](auditoria_por_etapas/resultados/evidencias/06-reval-pg18-20261114T213329260785Z.json), [14-G servidor](auditoria_por_etapas/resultados/evidencias/14-G-20261113/servidor/INFORME.md), [14-G navegador](auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/RESUMEN.md).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Clave UUID11111111-1111-4111-8111-111111111111; lote C, cantidad 10, costo6; otra clave22222222-2222-4222-8222-222222222222; contador0; variante contador99999999.

1. Confirmar; perder la respuesta y reintentar igual.
2. Reenviar misma clave con cantidad 11 y con otro actor.
3. Recibir de nuevo el lote comercial C con segunda clave y misma caducidad.
4. Probar cantidad 0 y corregir conservando clave.
5. Solapar dos envíos iguales en PostgreSQL; probar agotamiento de contador.

**Resultados esperados:** Primera recepción R-00000001; reintento recupera la misma sin nuevos efectos; divergencia/actor ajeno rechaza sin filtrar datos. Otro ingreso real conserva identidad/procedencia distinta. Inválido no consume clave exitosa; corrección puede confirmar. Carrera crea una sola recepción. Contador agotado informa capacidad y no muta; nunca reinicia o reutiliza referencia.

<a id="contrato-DEC-11-MODELO-AUDITORIA-VENTAS"></a>

### DEC-11-MODELO-AUDITORIA-VENTAS · Venta, lotes, caja e historia

**Requisito existente.** RN-25 exige asignaciones de lote; diseño §2.5 exige snapshots vendedor/caja. El diagnóstico previo mostró descuento de lotes con producto/precio/costo conservados y asignaciones/snapshots de vendedor y caja ausentes. La implementación14-F captura esos datos en el mismo cobro. Su cobertura y pendientes se registran en [ETAPA-14](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f).

**Diseño recomendado.** `SaleLotAllocation` por línea/lote y cantidad positiva; suma por línea=cantidad vendida. Añadir posición estable por línea y snapshots de nombre del vendedor/código de caja a la venta. Garantías de `inventory_movement`, `cash_movement`, `audit_event` e idempotencia se implementan de forma explícita o mediante equivalencia documentada y probada; retener `SaleDraftLine` no satisface trazabilidad de lotes. Para el tamaño del proyecto son adecuados movimientos append-only y vínculo único de movimiento de efectivo con venta, sin microservicios. Una clave/huella en la entidad confirmada puede satisfacer idempotencia sin tabla genérica adicional.

**Representación adoptada14-F.** `SaleLotAllocation` conserva línea, lote, cantidad positiva y fotografía del número comercial, vencimiento e instante de ingreso. FK protegidas y unicidad línea/lote acompañan la comprobación transaccional de suma asignada=cantidad vendida. `SaleLine.position` positiva fija el orden del borrador bloqueado. `Sale.seller_snapshot_name` y `cash_register_snapshot_code` guardan el encabezado al confirmar. La migración aditiva deja NULL en posiciones/cabeceras anteriores y la tabla de asignaciones histórica vacía. La consulta indica ausencia o asignación parcial y conserva el costoNULL como «No disponible».

**Ingreso de efectivo equivalente en R1.** Se adopta `Sale` como registro único del ingreso causado por una venta en efectivo. Su clave única, turno, autor, instante, correlativo y total identifican el evento. El cierre suma una vez cada `Sale.total_amount` del turno, dentro del bloqueo compartido con cobro. Venta, líneas, asignaciones y stock se confirman en la misma transacción. Reenvío devuelve la venta existente y fallo revierte todo el intento. Esta concreción técnica usa la equivalencia permitida por el contrato y la autorización de corrección de la sesión. Se comprobó apertura100+venta50=cierre150 tras reintento, además de los recorridosChrome. La concurrencia y caída real quedan para15. Movimientos manuales, anulaciones y otros medios conservan sus decisiones futuras. [Fundamento, alternativas y límites](auditoria_por_etapas/resultados/soporte/14-F-disposiciones.md).

<a id="DEC-11-MODELO-AUDITORIA-VENTAS-C-01"></a>

**DEC-11-MODELO-AUDITORIA-VENTAS/C-01.** Dada venta de 5 unidades con lotes3+2 elegibles, cuando confirma, entonces persisten dos asignaciones3/2, un movimiento efectivo por total, snapshots, costo, correlativo y descuento stock, atómicamente; sumaasignada=5.

<a id="DEC-11-MODELO-AUDITORIA-VENTAS-C-02"></a>

**DEC-11-MODELO-AUDITORIA-VENTAS/C-02.** Dado fallo al insertar cualquiera de esos elementos, cuando se revierte, entonces todas las tablas, contador y stock quedan como antes. Doble POST devuelve la misma venta.

<a id="DEC-11-MODELO-AUDITORIA-VENTAS-C-03"></a>

**DEC-11-MODELO-AUDITORIA-VENTAS/C-03.** Dados cambios posteriores de nombre, código, vendedor o caja, cuando se consulta constancia, entonces refleja la fotografía original y no el dato maestro actual; no muestra costos.

<a id="DEC-11-MODELO-AUDITORIA-VENTAS-C-04"></a>

**DEC-11-MODELO-AUDITORIA-VENTAS/C-04.** Dado legado sin asignaciones/snapshot/costo, cuando se consulta historia o margen, entonces identifica dato no disponible y no lo atribuye a un lote por aplicar FEFO al stock actual. Un backfill solo usa evidencia inequívoca y guarda procedencia.

Afecta VEN01c/02a/05a/05b, INV04, RN19/25/26/28 y diseño DB. La migración de costo histórico es `sales.0005`, no `sales.0004` (esta última añade producto).

**PROP-11-05 — Borrador después del cobro.** Se conserva temporalmente el comportamiento de retener líneas del borrador cobrado como soporte técnico, sin considerarlas historia canónica de venta ni asignaciones de lote. No se borran datos antiguos ni se crea un archivo adicional por iniciativa del implementador. La política de eliminación/retención se resuelve con SEC-15-RETENCION-01; las consultas usan Sale/SaleLine/snapshots/asignaciones. Dado un cobro confirmado, cuando se consulta historial, entonces no depende de que el borrador siga disponible ni permite volverlo a cobrar. Salir con borrador no cobrado conserva la regla específica de descarte de RN-30.

<a id="CP-DEC-11-MODELO-AUDITORIA-VENTAS-001"></a>
##### CP-DEC-11-MODELO-AUDITORIA-VENTAS-001 · Contrato DEC-11-MODELO-AUDITORIA-VENTAS

**Cubre:** DEC-11-MODELO-AUDITORIA-VENTAS/C-01, DEC-11-MODELO-AUDITORIA-VENTAS/C-02, DEC-11-MODELO-AUDITORIA-VENTAS/C-03, DEC-11-MODELO-AUDITORIA-VENTAS/C-04. **Estado:** EJECUTADO PARCIAL en primera pasada14-F, 13/11/2026. Asignaciones, fotografías, orden y legado contrastados en SQLite y Chrome. Fallos por excepción tras ocho puntos de escritura y reenvío secuencial comprobados. Concurrencia PostgreSQL, caída real e impresión física siguen pendientes.
**Evidencia de ejecución:** [Servidor14-F](auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/INFORME.md), [navegador14-F](auditoria_por_etapas/resultados/evidencias/14-F-20261113/navegador/RESUMEN.md), [build y cobertura](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f). Variante contractual A3/B2 vende5 y captura3/2, costo3, caja150 y stock0. Variante A3/B7 vende4 y captura3/1 con saldo6. El margen de REP07 permanece futuro. La migración de filas ficticias conserva datos antiguos y sus ausencias.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Variante de Leche: lotes A3+B2, promedio 3; venta5 a10, recibido50; turno100. Venta antigua con costo/asignación desconocidos.

1. Cobrar y leer asignaciones, movimiento y snapshots.
2. Editar maestros y consultar constancia.
3. Restaurar e inyectar fallo en cada inserción de la transacción; repetir doble POST.
4. Consultar el legado incompleto.

**Resultados esperados:** Asignaciones A3/B2 suman5; venta50, caja150 y stock0, promedio vigente0 con costo histórico3. Snapshot original estable sin costos en constancia. Cada fallo devuelve todas las tablas y contador al estado previo; reintento no duplica. Legado indica dato no disponible, nunca deduce lote aplicando FEFO actual.

<a id="contrato-DEC-11-DESCUENTOS-ALCANCE"></a>

### DEC-11-DESCUENTOS-ALCANCE · Nuevos cobros sin descuento discrecional

**Decisión/alternativas.** Se suspende el descuento libre nuevo hasta definir política concreta de promoción/autorización. Es más sencillo y evita entregar dinero al criterio de cualquier vendedor. Conservar el descuento libre tiene menor costo inmediato y riesgo comercial; construir aprobación con porcentajes arbitrarios añade complejidad injustificada. No inventar un máximo5/10/20% ni pedir contraseña compartida de ADMIN.

<a id="DEC-11-DESCUENTOS-ALCANCE-C-01"></a>

**DEC-11-DESCUENTOS-ALCANCE/C-01.** Dado un cobro nuevo, cuando el vendedor llega a confirmación, entonces no puede introducir descuento; el servidor solo admite descuento cero/ausente con semántica cero. Un importe positivo, negativo, inválido o manipulado se rechaza con «Los descuentos no están habilitados para nuevas ventas» sin mutación.

<a id="DEC-11-DESCUENTOS-ALCANCE-C-02"></a>

**DEC-11-DESCUENTOS-ALCANCE/C-02.** Dada venta histórica con descuento, cuando se consulta o se reintenta idempotentemente la confirmación ya realizada, entonces conserva importes/constancia anteriores, sin recalcularla a cero ni crear otra venta. La comprobación de identidad de reintento precede la aplicación de política de venta nueva.

<a id="DEC-11-DESCUENTOS-ALCANCE-C-03"></a>

**DEC-11-DESCUENTOS-ALCANCE/C-03.** Dada una nueva venta, entonces subtotal=total antes de cálculo interno base/IGV según RN27, y caja recibe total. Mantener campos históricos y reportes no habilita nuevas promociones.

Afecta VEN01b/01c/02a/05a/b, RN25/27, forms/services/templates/JS/tests. HU-VEN-03 sigue PDF/correo fuera de alcance; propuestas de HU descuento se archivan como futuro, no se reutiliza ese ID. Sin migración destructiva.

<a id="CP-DEC-11-DESCUENTOS-ALCANCE-001"></a>
##### CP-DEC-11-DESCUENTOS-ALCANCE-001 · Contrato DEC-11-DESCUENTOS-ALCANCE

**Cubre:** DEC-11-DESCUENTOS-ALCANCE/C-01, DEC-11-DESCUENTOS-ALCANCE/C-02, DEC-11-DESCUENTOS-ALCANCE/C-03. **Estado:** EJECUTADO en muestra 14-D, 13/11/2026. Formulario, servicio, reintento histórico y caja revalidados en SQLite, interfaz de cobro en Chrome. Variantes y límites precisos en el informe.
**Evidencia de ejecución:** [Corrección y alcance14-D](auditoria_por_etapas/resultados/soporte/14-D-disposiciones.md), [regresión final](auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/regresion-final.txt), [build](auditoria_por_etapas/resultados/evidencias/14-D-20261113/build-final.json). HTTP nuevo ejercita subtotal10.65 y Chrome14.20, histórico materializado subtotal20/descuento2/total18 y reintento previo/posterior al cierre. El resto de los contratos de venta conserva su estado.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Nueva venta2×10; descuento ausente,0,1,-1,abc. Venta histórica con subtotal20, descuento2,total 18 y clave confirmada.

1. Recorrer formulario nuevo y enviar cada variante desde petición directa.
2. Consultar la venta histórica y repetir su confirmación con la clave/contenido originales.

**Resultados esperados:** Nueva venta solo acepta cero/ausente: total 20, base16.95, IGV3.05; no ofrece descuento discrecional. Otros valores rechazan con «Los descuentos no están habilitados para nuevas ventas», sin mutación. Histórico/reintento conserva18 y su constancia, sin recalcular a20 ni duplicar stock/caja.

<a id="contrato-DEC-12-PERMISOS-HISTORIAL-Y-MENU"></a>

### DEC-12-PERMISOS-HISTORIAL-Y-MENU · Permisos comerciales

**Decisión.** ADMIN administra personal/catálogo/proveedores, realiza ajustes y bajas, consulta stock, cargas/recepciones/bajas/movimientos y toda venta/turno. ALMACENERO registra cargas/recepciones/bajas y consulta inventario/proveedores/catálogo necesarios, sin operar caja/ventas. VENDEDOR abre/prepara/cobra/cierra su turno, consulta sus propias ventas/turnos/constancias y productos vendibles en POS. Ninguno obtiene permisos técnicos por su rol comercial. ADMIN no cobra ni cierra turno ajeno mediante una excepción implícita. Se conserva el permiso actual de baja de ADMIN porque permite al responsable regularizar una pérdida comprobada; exige exactamente motivo, lote, autor, cantidad y controles del almacenero. La recepción/carga sigue reservada a ALMACENERO.

<a id="DEC-12-PERMISOS-HISTORIAL-Y-MENU-C-01"></a>

**DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-01.** Dado vendedorA y venta/turno deB, cuandoA solicita ID directo o cambia filtros, entonces no accede al registro ni sus agregados; ADMIN sí consulta los globales. Costo de compra nunca aparece en constancia para cliente, incluso abierta por ADMIN.

<a id="DEC-12-PERMISOS-HISTORIAL-Y-MENU-C-02"></a>

**DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-02.** Dado cada rol/visitante, cuando abre menú/página/URL directa, entonces disponibilidad y autorización coinciden; el encabezado ADMIN no ofrece «Nueva venta»/operar turno. Cuentas inactivas/revocadas no conservan acceso por cookie antigua.

<a id="DEC-12-PERMISOS-HISTORIAL-Y-MENU-C-03"></a>

**DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-03.** Dado catálogo administrativo, cuando VENDEDOR lo solicita, entonces se deniega; en POS accede a nombre/código/precio/existencia vendible sin costo. La futura consulta sin turno es VEN04, no una ampliación tácita.

RN07/29, PROD01, CAJA05 y VEN02a/05a/b. No cambia datos existentes. Pruebas de roles, propiedades, cabeceras, navegación de regreso y errores deben cubrir navegador y solicitudes directas. Distinguir acceso vendedor a sus turnos cerrados de las ventas de otro turno/usuario.

<a id="CP-DEC-12-PERMISOS-HISTORIAL-Y-MENU-001"></a>
##### CP-DEC-12-PERMISOS-HISTORIAL-Y-MENU-001 · Contrato DEC-12-PERMISOS-HISTORIAL-Y-MENU

**Cubre:** DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-01, DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-02, DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-03. **Estado:** EJECUTADO EN MUESTRA AISLADA (12-B, 14/11/2026) — CUMPLE en SQLite y Chrome (`ADMIN`, `ALMACENERO` `403`, `VENDEDOR A/B`, anónimo `302` y cookie revocada por desactivación UI en `/empleados/`, enlaces de menú por rol, cero costos en constancia y catálogo administrativo denegado a `VENDEDOR`). No cubre tráfico/retención global de Etapa `15`.
**Evidencia de ejecución:** [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b) · [Suite 12](auditoria_por_etapas/resultados/evidencias/12-tests-20261115T024447678082Z-34890834/test_output.txt) · [Chrome 12](auditoria_por_etapas/resultados/evidencias/12-browser-20261115T024214133045Z-c16c172f/browser-report.json).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** ADMIN, ALMACENERO, vendedorA, vendedorB y visitante; ventas/turnos de A y B; cookie de cuenta luego desactivada.

1. Recorrer menú y URLs de catálogo, POS, inventario, ventas, constancia y caja con cada identidad.
2. Alterar IDs/filtros hacia registros ajenos.
3. Desactivar A y repetir con su cookie anterior.

**Resultados esperados:** Permisos coinciden con RN-29 en menú y servidor. ADMIN consulta global sin operar turno; A solo propios y POS sin costos; ALMACENERO no cobra; visitante/revocado no acceden. Ninguna constancia expone costo, incluso para ADMIN. Totales y filtros respetan la misma propiedad que filas/detalles.

<a id="contrato-DOC-02-04"></a>

### DOC-02-04 · Personal, reset y confirmación

**Decisiones.** Nombre completo120, no único; correo normalizado único máx254. Crear/editar mantiene RN24 actual; un reset administrativo explícito permite desbloquear y revoca sesiones, con evento de quién/cuándo/cuenta afectada, nunca la clave. Reactivación/cambio de correo por sí solos no reinician silenciosamente una sanción vigente; conservar el plazo/bloqueo asociado a la cuenta. Para un desbloqueo legítimo usar acción confirmada y auditada. Se evita depender del correo automático futuro.

<a id="DOC-02-04-C-01"></a>

**DOC-02-04/C-01.** Dada cuenta con turno abierto o último ADMIN activo, cuando se cambia rol/desactiva, entonces se respetan las invariantes existentes y el rechazo no cambia cuenta/sesiones/turno.

<a id="DOC-02-04-C-02"></a>

**DOC-02-04/C-02.** Dado un cambio de estado, cuando ADMIN confirma un resumen de nombre/correo/efecto, entonces se aplica el destino explícito; al cancelar o repetir el destino no se invierte accidentalmente. La advertencia explica acceso/sesiones y restricciones reales.

<a id="DOC-02-04-C-03"></a>

**DOC-02-04/C-03.** Dado reset explícito válido, cuando confirma ADMIN, entonces cumple RN24, revoca cookies antiguas, guarda evento sin secreto y solo entonces permite nuevo login. Cambio de correo/reactivación conserva bloqueo hasta expiración o desbloqueo explícito. Probar bloqueo viejo/nuevo identificador y carreras de ingreso/desactivación.

<a id="DOC-02-04-C-04"></a>

**DOC-02-04/C-04.** Dado un usuario sin turno/borrador, cuando sale, entonces el mensaje no afirma que tiene uno. Con turno abierto y borrador, confirma descarte, no cierre de caja; cancelar no cambia nada.

RN12/17/24/29/30, USR02..05, AUTH03. Conservar política uniforme de identificadores inexistentes/inactivos de AUTH01/02. Antes de canonicalizar IDNA, producir informe de equivalencias y colisiones entre Unicode/punycode; no fusionar cuentas. Datos y pruebas de identidad deben usar cuenta ID estable para bloqueo/revocación, sin reset accidental al renombrar correo. Longitudes254/255,120/121, Unicode/espacios y normalización se comprueban en todas las capas.

<a id="CP-DOC-02-04-001"></a>
##### CP-DOC-02-04-001 · Contrato DOC-02-04

**Cubre:** DOC-02-04/C-01, DOC-02-04/C-02, DOC-02-04/C-03, DOC-02-04/C-04. **Estado:** EJECUTADO PARCIAL en sublote 02-E (segunda pasada acotada, 14/11/2026): `C-01`, `C-02`, `C-03` y `C-04` verificados con servidor (`652/652`), Chrome real (multi-navegador, desktop `1366×768` y móvil `390×844`) y PostgreSQL `18.4` (`5/5`); permanecen abiertos el informe de colisiones Unicode/punycode previo a una eventual canonicalización IDNA y la verificación en PostgreSQL `17`.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Último ADMIN activo; vendedorA con turno abierto; cuenta B bloqueada por 5 fallos; clave nueva ficticia PruebaNueva9!; sesiones de B en2 navegadores.

1. Intentar degradar/desactivar último ADMIN y A.
2. Revisar/cancelar/confirmar destino explícito de B y repetirlo.
3. Cambiar correo/reactivar B; intentar ingresar durante bloqueo.
4. Confirmar reset/desbloqueo explícito y comprobar cookies/evento.
5. Salir con y sin turno/borrador.

**Resultados esperados:** Invariantes rechazan sin mutar cuenta/sesión/turno. Cancelación no cambia; repetir destino no alterna. Correo/reactivación no limpian bloqueo. Reset válido aplica RN-24, revoca cookies y deja evento sin clave; desbloqueo solo por acción explícita. Mensaje de salida describe turno/borrador realmente existentes; confirmar descarta borrador y conserva turno.
**Evidencia de ejecución:** [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Servidor 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md) · [Navegador 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [PostgreSQL 02-E](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md) · [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py).

<a id="contrato-DOC-01-06"></a>

### DOC-01-06 · Seguridad técnica, tráfico y eventos

**Decisión de exposición.** Portal Django fuera de la navegación y acceso comercial; producción lo deshabilita o restringe a canal de mantenimiento autenticado y autorizado. No basta quitar enlace. Elegir configuración concreta al verificar despliegue; credenciales de mantenimiento no son cuentas compartidas de negocio.

<a id="DOC-01-06-C-01"></a>

**DOC-01-06/C-01.** Dado tráfico desde el punto de entrada comercial, cuando se solicita `/admin/` o `/admin/login/`, entonces no habilita otro camino de autenticación comercial ni elude límites. Probar perfiles staff/superuser ficticios y permisos por modelo en el canal autorizado.

<a id="DOC-01-06-C-02"></a>

**DOC-01-06/C-02.** Dado ingreso/salida/reset/cambio de rol/estado u operación crítica, cuando termina, entonces existe evento con fecha, actor cuando se conoce, acción, objeto, resultado y requestID sin secretos. Los eventos de mutación se guardan con la misma transacción de negocio; su emisión externa se hace tras commit o outbox, nunca como prueba de atomicidad por sí sola. El rechazo se deniega aunque falle el log; registrar diagnóstico sanitizado sin conceder acceso.

<a id="DOC-01-06-C-03"></a>

**DOC-01-06/C-03.** Dado error que contiene datos ficticios sensibles en `exc_info`/campos, cuando se registra, entonces no aparecen en destino/log. No confundir filtro con instrumentación.

**Investigación obligatoria.** SEC15TRAFICO: medir endpoint/punto de entrada/IP confiable y redes compartidas; proponer presupuesto/ventana y probar que limitar no bloquea toda la tienda tras NAT. SEC15RETENCION: separar contadores operativos de bitácora, finalidad/volumen/acceso y plazo; no borrar bloqueos activos ni contadores1–4 arbitrariamente. El contrato cuantitativo depende de información no disponible; sigue C, sin aprobación ficticia. Logging técnico actual no depende de pantalla HU-LOG-01 futura.

<a id="CP-DOC-01-06-001"></a>
##### CP-DOC-01-06-001 · Contrato DOC-01-06

**Cubre:** DOC-01-06/C-01, DOC-01-06/C-02, DOC-01-06/C-03. **Estado:** EJECUTADO PARCIAL EN MUESTRA 01-F (14/11/2026, build `2cef34b5...`) Y AMPLIADO EN SUBLOTE 02-E (14/11/2026) — ABIERTO (`C-01` INCUMPLE; `C-02` PARCIAL: en `02-E` `H02E-04` incorpora `IdentityAuditEvent` + `identity.audit` sanitizado en login/logout/alta/edición/estado/reset/desbloqueo/403/sesiones y conserva `"sessions_revoked": true`, pero `/admin/login/` sigue con `0` eventos y sin sumidero durable; `C-03` CUMPLE en sonda aislada; `SEC-15-TRAFICO`/`SEC-15-RETENCION`/`SEC-15-ADMIN`/`SEC-15-OBS` pendientes).
**Evidencia de ejecución:** [01-F, matriz y límites](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-f), [security-probes](auditoria_por_etapas/resultados/evidencias/01-F-20261114/security-probes.json), [chrome-manifest](auditoria_por_etapas/resultados/evidencias/01-F-20261114/chrome-manifest.json) (`C10–C19`), [postgresql-01f](auditoria_por_etapas/resultados/evidencias/01-F-20261114/postgresql-01f-latest.json) (`admin-bypass-concurrente`), [http-probes](auditoria_por_etapas/resultados/evidencias/01-F-20261114/http-probes.json) (`HTTP-07`), [orm-after](auditoria_por_etapas/resultados/evidencias/01-F-20261114/orm-after.json), [Informe 02-E (H02E-04)](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) y [Pruebas contrato 02-E](r1-pmv/identity/test_audit02e_contracts.py). No aprueba despliegue, throttling de entrada, retención ni restricción de `/admin/`.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Entrada comercial; perfiles ficticios staff/superuser y tres roles; error controlado cuyo exc_info contiene CANARIO-SECRETO-PRUEBA; requestID conocido.

1. Solicitar /admin/ y /admin/login/ desde entrada comercial.
2. Ejecutar ingreso, salida, reset, cambio de estado y mutación fallida.
3. Inspeccionar eventos persistidos y destino externo tras commit.
4. Provocar error sensible y fallo del registrador.

**Resultados esperados:** No existe vía comercial alternativa que eluda permisos/límites. Eventos guardan actor/fecha/acción/objeto/resultado/requestID, sin secretos. Mutación y evento transaccional confirman juntos; rollback no genera evento externo de éxito. CANARIO no aparece en logs. Fallo de log no concede acceso; diagnóstico sanitizado. UI LOG futura no excusa falta de eventos actuales.

<a id="contrato-DEC-10-BLOQUEO-INACTIVIDAD"></a>

### DEC-10-BLOQUEO-INACTIVIDAD · Puesto desatendido

**Decisión.** Seleccionar HU-VEN-01a/RN22 como requisito antes del piloto; pantalla de ventas bloquea tras300 segundos de inactividad válida. Preserva borrador/turno, no cobra/descarta/cierra. Reautentica mismo vendedor; logout conserva su regla distinta. Es costo medio y más adecuado que suponer que bloqueo de ingreso15min protege una sesión abierta.

<a id="DEC-10-BLOQUEO-INACTIVIDAD-C-01"></a>

**DEC-10-BLOQUEO-INACTIVIDAD/C-01.** Dado puesto autenticado inactivo300s, cuando intenta consultar datos de venta protegidos o mutar, entonces servidor exige reautenticación, incluso desde otra pestaña/HTTP directo. Un overlay JavaScript solo no cumple.

<a id="DEC-10-BLOQUEO-INACTIVIDAD-C-02"></a>

**DEC-10-BLOQUEO-INACTIVIDAD/C-02.** Dada actividad válida del usuario, entonces reinicia reloj del puesto; polling, reloj de cliente modificado y reintentos automáticos no lo renuevan. Definir estado de bloqueo por sesión, compartido entre sus pestañas.

<a id="DEC-10-BLOQUEO-INACTIVIDAD-C-03"></a>

**DEC-10-BLOQUEO-INACTIVIDAD/C-03.** Dada contraseña errónea/usuario distinto/inactivo, entonces no desbloquea ni pierde borrador; protege intentos conforme RN17 sin mostrar secretos. Tras reautenticar revalida precio/stock/turno antes de operar. Pruebas reloj, pestañas, suspensión/reanudación y rechazo sin mutación; no equiparar con sesión única futura.

<a id="CP-DEC-10-BLOQUEO-INACTIVIDAD-001"></a>
##### CP-DEC-10-BLOQUEO-INACTIVIDAD-001 · Contrato DEC-10-BLOQUEO-INACTIVIDAD

**Cubre:** DEC-10-BLOQUEO-INACTIVIDAD/C-01, DEC-10-BLOQUEO-INACTIVIDAD/C-02, DEC-10-BLOQUEO-INACTIVIDAD/C-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** A con turno/borrador; dos pestañas; 299 y 300 segundos; polling cada30s; reloj cliente manipulado; A/B/inactivo y cinco contraseñas erróneas.

1. Suspender interacción hasta 300s manteniendo polling.
2. Reanudar pestaña y enviar petición directa.
3. Probar identidad distinta, incorrecta e inactiva.
4. Desbloquear A válidamente después del plazo permitido; variar precio/stock durante bloqueo.

**Resultados esperados:** Servidor protege datos/operaciones de la sesión desde300s; pestañas comparten bloqueo. Polling/reloj cliente no reinician actividad. Errores no pierden borrador ni abren acceso, aplican RN-17. Reautenticación correcta conserva turno/borrador y exige revisar precio/stock cambiado antes de cobro.

<a id="contrato-DEC-05-LOTE-ESPACIOS"></a>

### DEC-05-LOTE-ESPACIOS · Identidades y límites de inventario

**Decisión.** Número comercial máx64, trim/mayúsculas/espacios consecutivos→uno, sin borrar guiones/separadores ni fusionar `AB 12` con `AB12`. Conservar presentación y original si necesario para trazabilidad. Antes de migrar, listar colisiones por producto/recepción; resolver con evidencia, no automáticamente.

<a id="DEC-05-LOTE-ESPACIOS-C-01"></a>

**DEC-05-LOTE-ESPACIOS/C-01.** Dadas variantes ` ab  12 ` y `AB 12`, cuando se comparan dentro de la misma recepción, entonces son el mismo identificador normalizado y la repetición se rechaza; `AB12` sigue distinta. Misma identidad comercial en otra recepción se rige por DOC03AI.

<a id="DEC-05-LOTE-ESPACIOS-C-02"></a>

**DEC-05-LOTE-ESPACIOS/C-02.** Dada carga/recepción, entonces cantidad entera1..999999, costo decimal0.0001..9999999.9999 (máx4 decimales), vencimiento>hoy Lima, código de lote1..64. Rechazar bool como entero, NUL, exponentes, signos ambiguos, precisión excedida y lote inexistente en operaciones que lo requieran.

Se ratifica el límite técnico de vencimiento hasta el aniversario de hoy+20 años; si el aniversario cae en día inexistente, usar el último día de ese mes, como `Lot.latest_expiration_date`. No es vida útil prescrita por ley. La UI actual ofrece cuatro tarjetas: omitir filas totalmente vacías si queda al menos una válida, validar simultáneamente las no vacías y rechazar `management_form` manipulado sin500. Cuatro tarjetas visibles no se convierte en máximo de negocio nuevo por inferencia. Límite defensivo de tamaño de solicitud/formset se verifica en seguridad antes de despliegue.

<a id="DEC-05-LOTE-ESPACIOS-C-03"></a>

**DEC-05-LOTE-ESPACIOS/C-03.** Dada cantidad mínima/ máxima y errores por campo, cuando se corrige el formulario, entonces preserva los valores válidos y muestra el error junto al campo/resumen accesible, sin consumir una clave exitosa. Probar medianoche UTC/Lima, producto/categoría/proveedor inactivados entre vista y POST.

<a id="CP-DEC-05-LOTE-ESPACIOS-001"></a>
##### CP-DEC-05-LOTE-ESPACIOS-001 · Contrato DEC-05-LOTE-ESPACIOS

**Cubre:** DEC-05-LOTE-ESPACIOS/C-01, DEC-05-LOTE-ESPACIOS/C-02, DEC-05-LOTE-ESPACIOS/C-03. **Estado:** EJECUTADO PARCIAL en muestra aislada (14-G + revalidación ETAPA-06 + revalidación `05-M` 14/11/2026): C-01 (espacios consecutivos, `AB12` distinto, legado `OLD  CODE`, `" ab  12 "` vs `"AB 12"` y restricción SQLSTATE `23505` en carga inicial PG `18.4`), C-02 (`25` fronteras HTTP `1..64/65`, `1..999999`, `0.0001..9999999.9999`, `bool`, `\x00`, `1e2`, `5` dec., dígitos árabes, +20 años/bisiesto y límites máximos en PG `18.4`, más fronteras de carga inicial a `23:30` Lima) y C-03 (medianoche UTC/Lima `04:59:59Z`/`05:00:00Z`, desactivación/revocación concurrente PG `18.4`, `TOTAL_FORMS=5`, `management_form` alterado, y preservación de sentinel tras proveedor desactivado en carga inicial; hallazgos: `min_num=1` en `stock_entry_form.html` y divergencia `OBS-05M-01` `max_length=64` crudo en `LotInputForm` vs normalizado en `confirm_initial_load`). Pendientes: colisiones en base operativa, resumen accesible arriba y `PG 17`. [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114) · [Informe 05-M](auditoria_por_etapas/resultados/ETAPA-05.md#reval-05m-20261114) · [Evidencia 14-G](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g).
**Evidencia de ejecución:** [ETAPA-06 servidor](auditoria_por_etapas/resultados/evidencias/06-reval-server-20261114T212733200909Z-caa926fa/report.json), [ETAPA-06 Chrome](auditoria_por_etapas/resultados/evidencias/06-reval-browser-20261114T212745468050Z-dce3e1b1/browser.json), [ETAPA-06 PG 18.4](auditoria_por_etapas/resultados/evidencias/06-reval-pg18-20261114T213329260785Z.json), [PG 18.4 05](auditoria_por_etapas/resultados/evidencias/05-postgresql-20261115T023932813038Z.json), [Verificación 05-M](auditoria_por_etapas/resultados/evidencias/05-M-reval-20261114T213817Z-f64f6a5a.json), [Chrome multirol 05](auditoria_por_etapas/resultados/evidencias/05-browser-20261114T213832599628Z-a1ecc756/browser.json), [14-G servidor](auditoria_por_etapas/resultados/evidencias/14-G-20261113/servidor/INFORME.md), [14-G navegador](auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/RESUMEN.md).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Lotes « ab  12 », «AB 12», «AB12»; longitudes0/1/64/65; cantidades0/1/999999/1000000/true; costos0/0.0001/9999999.9999/10000000/1e2/1.00001; vencimiento hoy/mañana/aniversario20 años/+1día; hoy Lima12/11/2026.

1. Enviar variantes independientes por UI y petición directa.
2. Desactivar producto/categoría/proveedor entre formulario y POST.
3. Alterar management form, enviar una fila válida más filas vacías y probar más de cuatro lotes válidos.
4. Repetir alrededor de medianoche UTC y Lima.

**Resultados esperados:** Normaliza a AB 12: duplicado interno rechaza; AB12 distinto. Solo rangos/tipos/fechas válidos; boolean, NUL, exponente y precisión excesiva rechazan íntegros con error junto al campo y valores válidos conservados. Límite fecha20 años por aniversario; cuatro tarjetas no son máximo comercial. Filas vacías se omiten si existe una válida; management form inválido nunca500. Estado obsoleto no ingresa stock.

<a id="contrato-DEC-04-RUC-VALIDACION"></a>

### DEC-04-RUC-VALIDACION · Proveedor y estado explícito

**Decisión.** RUC:11 dígitos ASCII, único; esto valida formato, no existencia/estado SUNAT. Nombre1..160 normalizado para presentación (no único por homonimia), teléfono opcional hasta 20 con el patrón vigente de formulario. El contrato no promete validación fiscal ni obliga integración externa. Costo bajo y apropiado para control interno.

Nombre debe contener al menos una letra o número; colapsar separadores blancos y rechazar NUL. Teléfono, cuando no está vacío, admite solo dígitos ASCII, espacios y signos `+ - ( )`, con al menos un dígito; colapsar espacios. Mostrar teléfono en lista (guion si falta). Búsqueda con NUL devuelve error controlado y cero filas, con opción de limpiar; foco en primer campo inválido y alerta accesible. Estos detalles implementados en muestras se ratifican desde este corte, sin atribuir aprobación comercial previa.

<a id="DEC-04-RUC-VALIDACION-C-01"></a>

**DEC-04-RUC-VALIDACION/C-01.** Dados proveedores homónimos, cuando se seleccionan/consultan recepción y registros, entonces nombre+RUC distinguen inequívocamente. El proveedor histórico inactivo permanece visible; solo los activos se eligen para nueva recepción, o se indica sin proveedor.

<a id="DEC-04-RUC-VALIDACION-C-02"></a>

**DEC-04-RUC-VALIDACION/C-02.** Dado POST de estado, cuando omite destino o envía otro valor, entonces rechaza; al repetir `activo=false`, permanece inactivo, no alterna. Actor ADMIN se revalida dentro de transacción; ALMACENERO consulta sin cambiar datos maestros.

<a id="DEC-04-RUC-VALIDACION-C-03"></a>

**DEC-04-RUC-VALIDACION/C-03.** Dado RUC inválido/duplicado o proveedor inactivado antes de confirmar entrada, entonces error claro y sin mutación; no convertir opción rechazada en omisión silenciosa. Describir «formato válido» sin insignia «validado SUNAT».

RN12 no gobierna proveedor; referenciar PROV01/02/04 y contrato de recepción. PROV03 edición sigue futuro. Revisar colisiones sin eliminar registros.

<a id="CP-DEC-04-RUC-VALIDACION-001"></a>
##### CP-DEC-04-RUC-VALIDACION-001 · Contrato DEC-04-RUC-VALIDACION

**Cubre:** DEC-04-RUC-VALIDACION/C-01, DEC-04-RUC-VALIDACION/C-02, DEC-04-RUC-VALIDACION/C-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Dos «Distribuidora Sol» con RUC20123456789/20987654321; teléfono+51 999 111 222; destino false/omitido/inválido; variante RUC10 dígitos/duplicado/Unicode.

1. Crear y distinguir homónimos.
2. Desactivar proveedor con destino false y repetir; probar omitido.
3. Confirmar recepción con proveedor desactivado tras abrir formulario.
4. Consultar historia y texto de validación RUC.

**Resultados esperados:** Homónimos permitidos y distinguidos por nombre+RUC; teléfono visible. Solo11 dígitos ASCII únicos, sin certificar SUNAT. False repetido mantiene inactivo; omitido/inválido rechaza sin cambio. Proveedor desactivado no se sustituye silenciosamente por ninguno; recepción rechazada completa. Historia conserva proveedor original.

<a id="contrato-RN-05"></a>

### RN-05 · Baja, ajuste y constancia

**Decisión.** Registrar causa real: vencimiento si se descarta por caducidad; daño solo antes de vencer; robo/faltante independiente de fecha, siempre con explicación y lote. No forzar vencimiento cuando se denuncia robo de unidades vencidas. Baja ADMIN o ALMACENERO; ajuste físico solo ADMIN; el estado comercial inactivo no impide corregir existencias reales. VENDEDOR nunca regulariza stock.

**Entradas.** Baja: lote, cantidad entera1..999999<=disponible, motivo de catálogo, explicación obligatoria daño/robo, clave. Ajuste: diferencia entera no cero en[-999999,999999], saldo no negativo; motivo1..300 sin NUL; lote existente o nuevo con fecha fiable/costo según DOC03AH. Existencia vencida encontrada puede registrarse por ajuste como **no vendible**, nunca recepción/carga inicial. Si no hay fecha fiable, se rechaza registro del lote y se investiga; no inventar fecha para permitir venta.

Para esta versión, el ajuste se habilita para productos con carga inicial confirmada. Evita que un ajuste previo sea sobrescrito por la fórmula de la primera carga. El arranque de un producto que solo tiene existencias vencidas y ninguna carga inicial necesita un procedimiento de apertura de inventario antes de admitirlo: se conserva como investigación de datos/operación, no se inventa una carga con unidades vendibles. Ese caso no puede pasar silenciosamente por recepción ordinaria.

<a id="RN-05-C-01"></a>

**RN-05/C-01.** Dado lote vencido con faltante comprobado, cuando ALMACENERO confirma robo con explicación, entonces baja por robo y conserva fecha/estado vencido; sin explicación rechaza. La baja no altera precio/caja/ventas y usa costo de salida de RN14.

<a id="RN-05-C-02"></a>

**RN-05/C-02.** Dado conteo ADMIN de lote nuevo, cuando aporta vencimiento fiable/motivo/costo requerido, entonces crea origen AJUSTE identificable, aumenta stock físico y solo cuenta como vendible si cumple estado y vencimiento. No consume una carga inicial ni simula compra.

<a id="RN-05-C-03"></a>

**RN-05/C-03.** Dada confirmación de baja, entonces hay constancia dedicada inmutable de referencia/fecha/autor/producto/lote/cantidad/motivo/explicación, consultable por ADMIN/ALMACENERO e imprimible si corresponde; no es ticket fiscal. HU-INV-02/CA-04 ya lo exige.

<a id="RN-05-C-04"></a>

**RN-05/C-04.** Dada concurrencia venta/baja/ajuste o doble POST, entonces no hay stock negativo ni duplicación; datos rechazados quedan intactos y reintento válido devuelve resultado anterior. Ajuste nuevo requiere pruebas de unicidad/colisiones.

**Concreción técnica14-I, primera pasada.** La baja existente conserva su correlativo B y guarda una clave UUID única, huella canónica de lote/cantidad/causa/explicación normalizada y fotografías de nombre/código/unidad de producto, responsable, número/vencimiento de lote y referencia de origen. Son datos de la confirmación, no lecturas posteriores de maestros. Cantidad, motivo, explicación, fecha y costo de salida ya pertenecen a la baja. Campos nuevos NULL representan registros anteriores; la consulta muestra lo que se conserva y no reconstruye historia desde nombres actuales. Se reutiliza StockWriteOff; no se añade historial global ni una nueva HU.

HTTP exige UUID válido; error no consume la clave. El servicio interno sin clave representa una operación nueva; para reintento debe enviarse la clave explícita. La misma clave/actor/contenido recupera la constancia aun tras otra sesión, agotamiento del stock, vencimiento o desactivación comercial; empleado revocado se deniega. Contenido o actor distintos rechazan sin mutación. La operación persistente sustituye para mermas la deduplicación temporal por sesión; los ajustes conservan implementación y pendiente propios. La transacción incluye clave, baja, fotografía y stock/costo; no garantiza concurrenciaPG por el solo uso de SQLite.

La constancia dedicada `/inventario/bajas/{UUID}/` y el enlace desde movimientos son de solo consulta para ADMIN/ALMACENERO. Muestran costo unitario de salida a4decimales, origen conocido o ausencia y la leyenda «Constancia interna de merma. No es un comprobante de pago.». Incluye impresión web; dispositivo físico y resistencia a modificación SQL directa se verifican aparte. No inferir aceptación fiscal/comercial de esta salida. [Fundamento, alternativas y alcance14-I](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).

Afecta INV02/03, RN03/04/05/14/20/29, DOC03AI. No añadir pantallas de cuarentena/recall/retiro proveedor de las propuestas RET a este alcance.

<a id="CP-RN-05-001"></a>
##### CP-RN-05-001 · Contrato RN-05

**Cubre:** RN-05/C-01, RN-05/C-02, RN-05/C-03, RN-05/C-04. **Estado:** EJECUTADO en muestras14-CIERRE: C01..03 y reintentos secuenciales/concurrentes de merma/ajuste con19casosPG complementarios. El contrato transversal no acredita toda concurrencia posible, recuperación ante caída ni operación.
**Evidencia de ejecución:** Corte vigente14-CIERRE. [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt), [PostgreSQL](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.
**Evidencia de ejecución:** [Servidor14-I](auditoria_por_etapas/resultados/evidencias/14-I-20261114/servidor/INFORME.md), [Chrome14-I](auditoria_por_etapas/resultados/evidencias/14-I-20261114/navegador/RESUMEN.md).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** E vencido3 unidades; baja por robo1 con/sin explicación; ajuste ADMIN+2 a lote nuevo con fecha fiable; producto inactivo con carga confirmada; dos conexionesPG.

1. Registrar robo explicado y consultar constancia.
2. Restaurar y probar sin explicación y DAÑO en vencido.
3. Registrar ajuste positivo, incluida variante vencida no vendible.
4. Solapar venta/baja/ajuste y reintentar la misma operación.

**Resultados esperados:** Robo explicado conserva causa real, lote/autor/fecha/costo; tiene constancia de merma inmutable dedicada. Sin explicación/daño vencido rechazan. Ajuste de ADMIN tiene origen propio; no simula compra y permite saneamiento físico de inactivos. Cantidad recibida original no se reescribe. Carreras sin negativos/duplicados; promedio RN-14 y caja/ventas originales preservados.

<a id="contrato-DEC-08-KARDEX-COMPRAS"></a>

### DEC-08-KARDEX-COMPRAS · Movimientos, saldos y filtros

**Requisito.** HU-INV-04 es movimientos/Kardex; HU-INV-06 es historial de ajustes. Completar movimiento cronológico con saldo, referencia de recepción/carga/venta/baja/ajuste, responsable y lote; filtros de tipo/fecha definidos en HU. Referencia SOL solo cuando exista ese flujo, no inventada para entrada directa.

<a id="DEC-08-KARDEX-COMPRAS-C-01"></a>

**DEC-08-KARDEX-COMPRAS/C-01.** Dada secuencia de movimientos conocidos, cuando se consulta período/tipo, entonces muestra orden ascendente total por instante+ID y saldo inicial del período/saldo resultante correcto. Filtrar filas no recalcula el saldo real ignorando movimientos excluidos; explicar saldo de apertura/cierre y total filtrado.

<a id="DEC-08-KARDEX-COMPRAS-C-02"></a>

**DEC-08-KARDEX-COMPRAS/C-02.** Dada venta multilote, entonces su salida se puede atribuir a las asignaciones persistidas. Un lote legado no asignado se identifica como desconocido; no presentar asociación inferida como comprobada.

<a id="DEC-08-KARDEX-COMPRAS-C-03"></a>

**DEC-08-KARDEX-COMPRAS/C-03.** Dados ADMIN/ALMACENERO, entonces consulta no muta; VENDEDOR no obtiene costos. Aplicar paginación estable25 con filtros preservados y totales calculados sobre conjunto filtrado, no solo página.

Depende de RN25, DOC03AI/AH y diagnóstico de historia. Crear un saldo inicial de corte con procedencia si no se puede reconstruir pasado, después de autorización de datos; no inventarlo en esta fase. INV05/06 completas siguen futuras.

**Concreción técnica14-H2, dentro de la delegación de integración.** La consulta deriva eventos desde líneas originales de carga/recepción, asignaciones de venta, bajas y ajustes, y comprueba cada lote contra su cantidad disponible. Origen ausente/inconsistente, asignación incompleta, identidad histórica ambigua, secuencia negativa o discrepancia por lote impiden mostrar un saldo reconstruido como fiable. No se calcula una apertura artificial desde el stock actual. Cantidades conocidas pueden seguir mostrándose con su procedencia; variación del filtro es «No disponible» si incluye cantidad o identidad no demostrada.

Período opcional con Desde/Hasta de fecha y hora localLima al minuto; ambas o ninguna, ISO YYYY-MM-DDTHH:mm, máximo16caracteres, espacios exteriores normalizados. Minuto final incluido. Tipos: Todos, Entradas, Ventas, Mermas, Ajustes y Todas las salidas (venta/merma/ajuste negativo). Apertura/cierre consideran todos los tipos del período; saldo de fila se calcula antes del filtro. Orden ascendente por instante e ID estable de origen; se añade tipo al ID para desempatar identificadores iguales entre tablas. Páginas25 y variación del conjunto filtrado completo, nunca solo de página. La página omitida/vacía es1; solo enteroASCII positivo de hasta9dígitos, fuera de rango informa error sin devolver otra página silenciosamente. Desde/hasta/tipo/page repetidos se rechazan. Consulta inválida conserva valores y errores sin presentar filas o resúmenes como resultado válido. No son límites de cantidades del negocio.

Se mantiene el monolito y se evita un segundo saldo mutable o una tabla genérica de eventos. Las consultas del historial completo tienen costo proporcional al volumen; paginar la salida no acredita rendimiento para todo el catálogo. Consistencia concurrente de lecturas y volumen requieren etapa15. Esta concreción realiza criterios ya seleccionados y no añade selección comercial ni autorización para datos operativos. [Inventario14-H2](auditoria_por_etapas/resultados/soporte/14-H2-inventario.md).

<a id="CP-DEC-08-KARDEX-COMPRAS-001"></a>
##### CP-DEC-08-KARDEX-COMPRAS-001 · Contrato DEC-08-KARDEX-COMPRAS

**Cubre:** DEC-08-KARDEX-COMPRAS/C-01, DEC-08-KARDEX-COMPRAS/C-02, DEC-08-KARDEX-COMPRAS/C-03. **Estado:** EJECUTADO en muestra14-H2 paraC01/C02/C03: SQLite secuencial yChrome, saldos conocidos, filtros, páginas, legado y permisos. ConcurrenciaPG, estabilidad entre páginas mientras cambian datos y volumen requieren15; no se transfieren garantías delbuild14-F.
**Evidencia de ejecución:** [Servidor14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/servidor/INFORME.md), [Chrome14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/navegador/RESUMEN.md). Antecedente14-F conservado: [Movimientos de venta y legado](auditoria_por_etapas/resultados/evidencias/14-F-20261113/navegador/final2/movimientos-confrontados.json), [rechazos y GET sin mutación](auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/INFORME.md).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Cursor adicional14-H2:10+10+5−22−1=2, venta22 con asignaciones10/10/2; período posterior alsegundo ingreso abre20/cierra2. Movimientos conocidos +20,+10,-5,-2,+1 con asignaciones;26filas para paginar; legado sin asignación; ADMIN/ALMACENERO/VENDEDOR.

1. Consultar orden completo y saldos; filtrar solo salidas y período intermedio.
2. Navegar páginas con empate de instante.
3. Abrir venta multilote y legado sin evidencia.
4. Comparar base antes/después de GET.

**Resultados esperados:** Saldos20,30,25,23,24; filtros no reconstruyen falso saldo omitiendo entradas. Paginación25 con orden instante+ID y filtros/totales del conjunto completo. Salidas enlazan asignación persistida; legado desconocido rotulado. GET no muta y VENDEDOR no obtiene costos.

<a id="contrato-DEC-07-VENCIDOS-FILTRO"></a>

### DEC-07-VENCIDOS-FILTRO · Alertas y panel mínimo

**Decisión.** Separar «Próximos a vencer» (hoy<fecha<=hoy+días) de «Vencidos» (fecha<=hoy, stock físico>0), permitiendo consulta conjunta rotulada. Inventario vencido/inactivo sigue visible como problema físico. Alerta de reposición bajo mínimo aplica a producto y categoría activos con vendible<=mínimo. Panel mínimo muestra datos del día Lima, umbral30 días rotulado, vencidos y turnos según rol; no se afirma entregar DASH/REP completos.

<a id="DEC-07-VENCIDOS-FILTRO-C-01"></a>

**DEC-07-VENCIDOS-FILTRO/C-01.** Dado producto inactivo con unidades vencidas, entonces figura en vencidos con badge inactivo/no vendible; no dispara compra/reposición por stock bajo. Reactivar categoría no reactiva un producto suspendido.

<a id="DEC-07-VENCIDOS-FILTRO-C-02"></a>

**DEC-07-VENCIDOS-FILTRO/C-02.** Dado filtro días, entonces se valida entero ASCII en el rango de pantalla existente y se mantiene frontera temporal de Lima; al cambiar filtro, etiquetas/conteos/listado explican el mismo conjunto. No inventar1d/30d como obligación legal.

Rango ratificado del filtro actual:1..3650, predeterminado30; parámetro inválido informa y usa30 sin500. El número de días no cambia la frontera de lotes ya vencidos. OBS-00-15 ya tiene columna numérica `Existencias vigentes (UND)` en `catalog/templates/catalog/product_list.html`; no se pide crearla de nuevo. La prueba visual actual de todas sus combinaciones sigue en la matriz correspondiente.

<a id="DEC-07-VENCIDOS-FILTRO-C-03"></a>

**DEC-07-VENCIDOS-FILTRO/C-03.** Dado panel ADMIN, entonces totales diarios no se presentan como reporte por período, margen, gráfico, ranking o solicitudes implementadas. Medir volumen antes de aprobar índice parcial; un EXPLAIN pequeño no determina necesidad productiva.

**Precisión de presentación aceptada, primera pasada13-B (13/11/2026).** Bajo RN-06 y CT-COHERENCIA-UI, la alerta explica que incluye stock en el mínimo o por debajo; una entrada de mercadería registra bienes recibidos, sin sugerir autorización de compra. Se conserva el enlace al historial general y se identifica que abre todas las fechas; para cotejar ventas diarias se indica aplicar Fecha exacta con el día de Lima del panel. Esta elección aprovecha la consulta vigente y no selecciona reportes futuros. Una consulta fallida conserva su condición de error y ofrece recuperación; no sustituye sus cifras por ceros ni revela detalles técnicos. Son precisiones técnicas aceptadas dentro del encargo13-B, no cambios de política ni evidencia de ejecución por sí mismas. [Disposición y comprobaciones](auditoria_por_etapas/resultados/soporte/13-B-disposiciones.md).

**Precisión de consistencia aceptada,13-B.** La reproducción en PostgreSQL con un commit entre las lecturas mostró cifras de estados incompatibles. Las siete cifrasADMIN o las tresALMACENERO deben obtenerse mediante una misma consulta con fechaLima común, para compartir la instantánea de esa sentencia. Este ajuste técnico deCT-COHERENCIA-UI evita la mezcla demostrada dentro del resumen; no promete que un destino abierto después comparta la instantánea, actualización automática, aislamiento global de toda la página ni garantía de atomicidad de operaciones ajenas al panel. La reproducción y revalidación se acotan a la versión y conexiones documentadas en13-B; PostgreSQL17 sigue siendo el motor objetivo.

**Revalidación técnica `07-B` (14/11/2026 Lima, sin edición de código del producto):** En `r1-pmv` (`f0d6fa81...` / `c7bfe1fa...`, idénticos en módulo `07`), se comprueba `H13-02` resuelto en `/productos/`, `/inventario/stock/` y contraste POS, una sola sentencia SQL en `_dashboard_summary` y separación `FUTURO (W)` de `HU-DASH-03`. Permanece abierto el incumplimiento de `DEC-07-VENCIDOS-FILTRO` y `HU-PROD-06/CA-03` porque `/productos/vencimientos/` mantiene una sola tabla combinada sin separar «Próximos a vencer» de «Vencidos» (alternativas A/B/C documentadas en [Disposiciones 07-B](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md)). La medición `PT-SEARCH-01` en PostgreSQL `18.4` (`2.001` productos / `20.002` lotes) muestra que un índice parcial experimental (`idx_lot_exp_avail_gt0`, `648 kB`) acelera los planes SQL (`Bitmap Index Scan`/`Index Only Scan`, `30–120 ms` SQL), pero el `95 %+` de la latencia HTTP (`3,56–3,63 s` mediana, `2,0–4,4 MB` HTML) proviene de renderizar tablas sin paginación e hidratar `20.002` lotes en Python; por tanto `PROP-07-IDX-01` requiere acompañarse de `PROP-07-ESCALA-PAGINACION-01` antes de aprobarse ([Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Benchmark PG 18.4](auditoria_por_etapas/resultados/evidencias/07-B-20261114/pg-bench-07b-20261115T024804Z.json)).

<a id="CP-DEC-07-VENCIDOS-FILTRO-001"></a>
##### CP-DEC-07-VENCIDOS-FILTRO-001 · Contrato DEC-07-VENCIDOS-FILTRO

**Cubre:** DEC-07-VENCIDOS-FILTRO/C-01, DEC-07-VENCIDOS-FILTRO/C-02, DEC-07-VENCIDOS-FILTRO/C-03. **Estado:** EJECUTADO PARCIAL en primera pasada (`07-B`, 14/11/2026 Lima): `C-01` (`H13-02` y cascada de categoría) y `C-03` (panel mínimo, roles y `PT-SEARCH-01` medido) CUMPLE en muestra aislada y PG `18.4`; `C-02` PARCIAL / INCUMPLE separación `DEC-07` porque `?dias=7` mezcla vencidos y próximos en una tabla única (`PG 17` pendiente).
**Evidencia de ejecución:** [Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Disposiciones 07-B](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md) · [Sondas 07-B](auditoria_por_etapas/resultados/evidencias/07-B-20261114/probes-07b.json) · [Chrome 07-B](auditoria_por_etapas/resultados/evidencias/07-B-20261114/browser-07b-summary.json) · [PG 18.4 07](auditoria_por_etapas/resultados/evidencias/07-postgresql-20261115T025829083471Z.json) · [Benchmark 20k PG 18.4](auditoria_por_etapas/resultados/evidencias/07-B-20261114/pg-bench-07b-20261115T024804Z.json).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Producto inactivo con E3 vencidas; Arroz activo5 mínimo 10; lotes futuros1/30/31 días; filtros1/30/3650/0/3651/abc; panelADMIN.

1. Consultar vencidos, críticos y próximos; cambiar días.
2. Reactivar categoría con producto individual suspendido.
3. Revisar rótulos/totales/enlaces del panel.

**Resultados esperados:** Vencido inactivo visible y no sugiere compra por stock bajo; crítico solo producto/categoría activos. Filtro1..3650, inválido informa y usa30; rótulos/listas/conteos coinciden en Lima. Reactivación no activa producto. Panel mínimo muestra su ventana30 y totales diarios; no promete reportes/ranking futuros.

<a id="CP-DEC-07-VENCIDOS-FILTRO-002"></a>
##### CP-DEC-07-VENCIDOS-FILTRO-002 · Panel mínimo por rol, fecha y estado de los datos

**Cubre:** DEC-07-VENCIDOS-FILTRO/C-03, CT-COHERENCIA-UI/C-02, CT-COHERENCIA-UI/C-03. **Estado:** EJECUTADO Y VERIFICADO en primera pasada, etapa 13-B-final, 13/11/2026; limitado al panel mínimo y las consultas descritas en este caso, con navegador, servidor y PostgreSQL 18.4. No aprueba CP001 ni todo CT-COHERENCIA-UI.
**Precondiciones:** Base aislada con sesiones independientes de ADMIN, ALMACENERO y VENDEDOR. Usar fecha local de Lima y un visitante sin sesión. Los descuentos precargados son históricos.
**Datos de prueba:** Tres ventas confirmadas el día local por S/ 10.01, 20.02 y 30.03, con descuentos de 0.01, 2.02 y 3.03. Una venta anterior y otra del día siguiente. Un turno abierto. Tres productos activos en mínimo o por debajo. Seis lotes con saldo positivo por vencer en 1–30 días y cinco vencidos con saldo. Incluir lotes al día 0, 30 y 31, con saldo cero y con producto o categoría inactivos. Preparar una nueva venta de S/ 7.10 sin descuento que deje otro producto justo en su mínimo.

1. Abrir Inicio en las tres sesiones. Comparar siete cifras de ADMIN con las filas de ventas, turnos, productos y lotes. Comparar las tres cifras de inventario de ALMACENERO con los mismos registros. Comprobar en VENDEDOR las opciones de su puesto y en visitante la redirección al ingreso.
2. Seguir desde el panel los enlaces de inventario, vencimientos e historial permitidos. Registrar filtros y fechas al aterrizar. Si el historial muestra todas las fechas, aplicar el día de Lima antes de comparar. Pedir como ALMACENERO una consulta de ventas y como VENDEDOR una de inventario. Comprobar respuesta, ausencia de datos ajenos y conservación de filas de negocio.
3. Mantener el panel abierto mientras VENDEDOR prepara la venta y luego la cobra. Volver a consultar como ADMIN y ALMACENERO. Comparar el valor antes de confirmar y después de recargar. Repetir con ventas y lotes ausentes para distinguir los ceros de una consulta fallida.

**Resultados esperados:** ADMIN ve 3 ventas, S/ 60.06 vendidos, S/ 5.06 de descuentos, 1 turno abierto, 3 productos críticos, 6 lotes próximos y 5 vencidos. ALMACENERO ve los tres conteos de inventario y el servidor limita la consulta a su rol. VENDEDOR accede solo a sus operaciones y consultas propias. La pantalla identifica la fecha de Lima, las cifras diarias y los conteos actuales, e indica que se actualizan al abrir o recargar. Preparar el borrador conserva las cifras. Tras cobrar, la nueva consulta devuelve 4 ventas, S/ 67.16, S/ 5.06 de descuentos y 4 productos críticos. Denegaciones y lecturas conservan ventas, turnos y lotes. Un conjunto vacío muestra sus ceros y un fallo debe conservar su condición de error.
**Evidencia de ejecución:** [Cierre de la primera pasada](auditoria_por_etapas/resultados/ETAPA-13.md#cierre-13-b-final) · [Navegador final por rol y estado](auditoria_por_etapas/resultados/soporte/13-B-final-navegador.md) · [Constancia del cobro por interfaz](auditoria_por_etapas/resultados/evidencias/13-B-final-20261113/I07-cobro-confirmado.jpg) · [Servidor poblado](auditoria_por_etapas/resultados/evidencias/13-B-servidor-20261113T164755068835Z/results.json) · [Servidor vacío](auditoria_por_etapas/resultados/evidencias/13-B-servidor-20261113T164757087079Z/results.json) · [PostgreSQL 18.4](auditoria_por_etapas/resultados/soporte/13-B-postgresql.md).

**Antecedente 13-B al 13/11, antes de recuperar el navegador:** el servidor revalidó cifras por rol, fecha Lima, textos de consulta general/recarga, vacíos reales, fallo y recuperación sin ceros, denegaciones y estados de cuenta/rol sin mutación. Los 100 casos de cada fixture se solapan y no son 200 pruebas únicas. El navegador reobservó ADMIN inicial, login, catálogo inactivo y vencimientos 30→1 antes de perder acceso. Ese corte dejó pendientes los tres roles finales, cobro por interfaz y vacíos/interacción; se conserva en los informes históricos y queda sustituido, para estos pendientes, por la evidencia siguiente. Los efectos por servicios de 13-A conservan su capa original.

**Cobertura final demostrada, 13-B-final, 13/11/2026 Lima:** [Navegador y mapa de casos](auditoria_por_etapas/resultados/soporte/13-B-final-navegador.md) · [Verificación de compatibilidad y persistencia](auditoria_por_etapas/resultados/evidencias/13-B-final-20261113/validacion-evidencia.json). Build `99686b95a2c1d612bd4944a6cc0e7d16ab601c3f73d142e546a5f0c8ca30e215`, sin cambios de producto respecto al final 13-B: ADMIN siete cifras, ALMACENERO tres y VENDEDOR sin resumen; login, catálogo inactivo, igualdad del mínimo y recepción; filtro 1/30/3650 y retorno de inválidos a 30 con mensaje; enlaces y conciliación del historial general con el día de Lima. En una fixture nueva independiente, el navegador preparó 2×S/3.55 sin cambiar ventas ni lote, confirmó total S/7.10 con efectivo S/10.00 y vuelto S/2.90, y comprobó tras recargar ADMIN 4/67.16/5.06/1/4/6/5, ALMACENERO 4/6/5 y lote 3→1; persistencia y recarga sin duplicado. Otra fixture realmente vacía, fallo de SELECT y recuperación en las cuatro consultas, accesos denegados, cuenta inactiva/rol inválido restaurados, D11 y foco/teclado a 390 px completan la muestra. Se conserva evidencia de servidor y PostgreSQL compatible por hashes; no se presenta como una nueva ejecución ni se suman suites solapadas. No certifica todos los módulos de destino, PostgreSQL 17, accesibilidad universal ni despliegue.

**PostgreSQL13-B:** [37/37 comprobaciones y6/6tests](auditoria_por_etapas/resultados/soporte/13-B-postgresql.md), con fronterasLima, vacíos, efectos de cobro por servicios y escrituras concurrentes independientes; snapshot de sentencia y volumen sintético declarado. [RegresiónSQLite160/160](auditoria_por_etapas/resultados/evidencias/13-B-20261113/regresion-final.txt). Las suites se solapan y no sustituyen navegador; PostgreSQL18.4 difiere del17previsto.

El caso se incorpora el 13/11 por el encargo de auditar el panel en ambos sentidos y por los contratos ya aceptados DEC-07, RN-06, RN-29 y CT-COHERENCIA-UI. Precisa la presentación y la prueba de las consultas del release vigente. Los reportes de período, Yape y actualización automática conservan su selección futura. [Planificación anterior, ocho archivos del corte](auditoria_por_etapas/resultados/evidencias/13-A-20261113/planificacion/antes.zip).

<a id="contrato-DEC-11-TOPE-EFECTIVO-FORM"></a>

### DEC-11-TOPE-EFECTIVO-FORM · Dinero y restricciones

**Decisión.** Venta nueva, efectivo entregado y apertura admiten hasta 9,999,999.99 soles; precio/cantidades deben generar total dentro del límite antes de confirmar. Mantener precisión2 y redondeo vigente. Saldo esperado/contado/cierre acumulado admite capacidad `numeric(14,2)` (hasta 999,999,999,999.99); no reutilizar el tope por operación para impedir cierre legítimo de suma de ventas. Diferencia puede ser negativa y debe equivaler a contado−esperado. Es un límite interno de interfaz/almacenamiento, no un umbral tributario.

<a id="DEC-11-TOPE-EFECTIVO-FORM-C-01"></a>

**DEC-11-TOPE-EFECTIVO-FORM/C-01.** Dados vacío/mínimo/máximo/máximo+0.01, exponente, signo extra, dígitos no ASCII y más de 2decimales, entonces UI/servicio responden igual y no hay mutación en rechazo. Dinero siempre Decimal/centavos, nunca float.

<a id="DEC-11-TOPE-EFECTIVO-FORM-C-02"></a>

**DEC-11-TOPE-EFECTIVO-FORM/C-02.** Dado acumulado válido de varias ventas que supera el tope de una operación, cuando se cierra, entonces no se rechaza por ese tope; rechazar antes una venta que excedería capacidad acumulada y explicar capacidad, sin bloquear cierre de datos válidos ya registrados.

<a id="DEC-11-TOPE-EFECTIVO-FORM-C-03"></a>

**DEC-11-TOPE-EFECTIVO-FORM/C-03.** Dada inserción/actualización directa en base de prueba, entonces checks impiden cantidad de borrador fuera de 1..999999, montos negativos donde no procedan y cierre incoherente. El check de cantidad>0 ya existe; PROP-10-04 exige añadir el máximo999999 faltante. Probar el signo negativo permitido de diferencia y límites del tipo.

Precio unitario nuevo no puede exceder el máximo de una venta. Diagnosticar precios legacy superiores antes de endurecer validación/constraints; no recortarlos ni reinterpretarlos automáticamente. El total y el efectivo revalidan su tope aunque cada precio individual sea válido.

PROP09DB01/PROP10-04, RN10/25/27, CAJA01/02 y VEN01c. Auditar datos antes de migración; no convertir NULL/inválido en cero sin evidencia.

**Concreción14-CIERRE, dinero.** Se separan los límites de nueva operación y acumulación; bajo el bloqueo del turno se comprueba apertura+suma de ventas confirmadas+nueva venta antes de escribir venta, contador o stock. Los reintentos históricos conocidos conservan sus importes originales hasta la capacidad14,2; no se aplican retroactivamente las prohibiciones nuevas de descuento ni el tope por operación. Esto no permite crear descuentos nuevos. Formularios y servicios rechazan formatos ambiguos antes de convertirlos. Los checks de cantidad y cierre/montos se acompañan de diagnóstico previo en migración, sin recorte ni backfill. Son restricciones de integridad de los contratos ya aceptados; la orden de corrección de14 habilita implementarlas, no migrar la base operativa.

<a id="CP-DEC-11-TOPE-EFECTIVO-FORM-001"></a>
##### CP-DEC-11-TOPE-EFECTIVO-FORM-001 · Contrato DEC-11-TOPE-EFECTIVO-FORM

**Cubre:** DEC-11-TOPE-EFECTIVO-FORM/C-01, DEC-11-TOPE-EFECTIVO-FORM/C-02, DEC-11-TOPE-EFECTIVO-FORM/C-03. **Estado:** EJECUTADO en primera pasada14-CIERRE: límites por operación/acumulados, formatos, recuperación histórica y checks probados en SQLite/Chrome/PostgreSQL18.4. Migración operativa no ejecutada.
**Evidencia de ejecución:** Corte vigente14-CIERRE. [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt), [PostgreSQL](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Montos vacío,0,0.01,9999999.99,10000000.00,1e2,++1,Unicode y 1.001; cierre acumulado10000000.00; diferencia-5; cantidad de borrador0/1/999999/1000000.

1. Validar UI/servicio según campo: apertura/contado≥0, precio>0 y efectivo≥total.
2. Cerrar acumulado que supera tope por operación pero cabe en numeric(14,2).
3. Intentar nueva venta que excede capacidad acumulada.
4. Insertar/actualizar valores inválidos directamente en base aislada y capturar checks.

**Resultados esperados:** Validaciones coherentes en todas las capas, usando Decimal. Venta/precio/efectivo/apertura tope9999999.99; cierre permite acumulado válido hasta 999999999999.99, diferencia negativa legítima. Exceso se rechaza antes de venta sin bloquear cierre válido. Check borrador exige1..999999 y no se atribuye como nuevo el mínimo ya existente. Rechazos sin efectos.

<a id="contrato-DEC-12-ORDEN-LINEAS-RECIBO"></a>

### DEC-12-ORDEN-LINEAS-RECIBO · Consulta estable y UX

**Decisión.** Conservar orden de líneas del borrador en la venta nueva mediante posición persistida, independiente del UUID. Turnos ordenan apertura descendente con desempate por ID. Para legado sin posición, usar orden determinista declarado, sin afirmar que recupera la secuencia original. Paginación25 y filtros estables en listados crecientes; no añadir índices sin medición.

<a id="DEC-12-ORDEN-LINEAS-RECIBO-C-01"></a>

**DEC-12-ORDEN-LINEAS-RECIBO/C-01.** Dadas líneasA,B,C con UUID aleatorios, cuando se confirma y reabre constancia, entonces conservaA,B,C y snapshots; igualdad de instante en dos turnos siempre produce mismo orden.

<a id="DEC-12-ORDEN-LINEAS-RECIBO-C-02"></a>

**DEC-12-ORDEN-LINEAS-RECIBO/C-02.** Dado filtro válido/fecha incompleta/invertida, cuando consulta historial, entonces cumple el contrato de rango, muestra error claro sin500 para inválidos, preserva parámetros al paginar y abre detalle seleccionado. HU-VEN-05b/CA-02 es filtros y CA-03 es detalle; no exige expandir líneas en lista.

<a id="DEC-12-ORDEN-LINEAS-RECIBO-C-03"></a>

**DEC-12-ORDEN-LINEAS-RECIBO/C-03.** Dado rol ADMIN, entonces no ve topbar de vendedor ni enlaces operativos denegados; VENDEDOR puede volver a sus ventas/turno. En futuro no implementado, indicar estado sin botón que prometa acción disponible.

<a id="DEC-12-ORDEN-LINEAS-RECIBO-C-04"></a>

**DEC-12-ORDEN-LINEAS-RECIBO/C-04.** Dado GET de borrador, entonces no guarda precio nuevo automáticamente. Si precio/disponibilidad cambió, POST explícito/revisión previa al cobro informa y requiere aceptar contenido actualizado, conservando firma/identidad de borrador y validación final.

Afecta VEN01b/02a/05a/05b, CAJA05, PROP10-03, PROP12PAGINACION y menús. Pruebas empates forzados, varias páginas, dos pestañas, teclado,390×844 y impresión; repetir un test sin empate no demuestra arreglo.

<a id="CP-DEC-12-ORDEN-LINEAS-RECIBO-001"></a>
##### CP-DEC-12-ORDEN-LINEAS-RECIBO-001 · Contrato DEC-12-ORDEN-LINEAS-RECIBO

**Cubre:** DEC-12-ORDEN-LINEAS-RECIBO/C-01, DEC-12-ORDEN-LINEAS-RECIBO/C-02, DEC-12-ORDEN-LINEAS-RECIBO/C-03, DEC-12-ORDEN-LINEAS-RECIBO/C-04. **Estado:** EJECUTADO EN MUESTRA AISLADA (12-B, 14/11/2026; amplía `14-F`) — CUMPLE en SQLite, Chrome (`1366×900`, `1366×768`, `390×844`, teclado e impresión `@media print`) y PostgreSQL `18.4` (orden 3 líneas inversas por `position` + aviso legado, desempate de turnos/ventas, paginación 25/26 con filtros y parámetros inválidos, revisión explícita tras cambio de precio entre pestañas y menús sin promesas falsas). No cubre `PG 17`, impresora física, volumen productivo (`Etapa 15`) ni despliegue operativo.
**Evidencia de ejecución:** [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b) · [Suite 12](auditoria_por_etapas/resultados/evidencias/12-tests-20261115T024447678082Z-34890834/test_output.txt) · [Chrome 12](auditoria_por_etapas/resultados/evidencias/12-browser-20261115T024214133045Z-c16c172f/browser-report.json) · [PG 18.4](auditoria_por_etapas/resultados/evidencias/12-pg-20261115T024551489938Z-daa4b807/pg-report.json) · [Orden y legado 14-F heredado](auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/INFORME.md).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Borrador líneas A,B,C con UUID desordenados; dos turnos con apertura idéntica;26ventas; precio cambia10→11; fechas incompletas/invertidas; ancho390×844.

1. Cobrar y reabrir/ imprimir constancia.
2. Repetir historial empatado y paginar con filtros.
3. Consultar borrador por GET tras cambio de precio; luego revisar y confirmar por POST.
4. Recorrer menú ADMIN/VENDEDOR con teclado y móvil.

**Resultados esperados:** Posiciones A,B,C persistidas; orden de turnos con desempateID; legado sin posición usa orden declarado, no finge orden original. Filtros inválidos muestran error sin500; navegación preserva parámetros. GET no cambia precio; POST exige revisión explícita antes de cobro. Menús solo ofrecen acciones propias; sin promesas de función futura disponible.

<a id="contrato-DOC-00-01"></a>

### DOC-00-01 · Alcance y gobierno Scrum

**Decisión.** Adoptar R1 de consolidación: nueve HU originales más las adicionales auditadas de identidad/catálogo/proveedores/inventario/historia y bloqueo de pantalla previo al piloto. La selección, prioridad y tamaño orientativo están en las fichas de esta fuente08;09 es una vista derivada. Conservar futuros y ocho ideas; no seleccionar SOL/Yape/reportes completos por estar escritos. Ratificar mínimos/nombres desde hoy, no fingir autorización anterior.

<a id="DOC-00-01-C-01"></a>

**DOC-00-01/C-01.** Dado cualquier HU del catálogo, entonces existe una única fila vigente en backlog, una fila por CA base en matriz y relación con encargos cuando cambian criterios. SP originales se identifican como estimaciones previas, no tamaño actualizado de trabajo restante.

<a id="DOC-00-01-C-02"></a>

**DOC-00-01/C-02.** Dados documentos01/02/03/07/08/09/14/16/20/21/CONTROL e informes00–12, entonces apuntan al mismo corte, separan historia y no mantienen dos estados actuales contradictorios.

<a id="DOC-00-01-C-03"></a>

**DOC-00-01/C-03.** Dado trabajo aceptado, entonces no se llama implementado hasta cambio autorizado, ni verificado hasta evidencia exacta. No asignar Sprint/fecha/persona/velocidad a partir de valores académicos viejos.

<a id="DOC-00-01-C-04"></a>

**DOC-00-01/C-04.** Dadas propuestas de límites/nombres de catálogo, entonces mínimo por defecto10, rango0..999999 y nombre producto único normalizado incluyendo inactivos preservan decisiones actuales; cualquier cambio requiere análisis de colisión y pruebas. Empleados/proveedores homónimos siguen permitidos: esa unicidad no se propaga a otras entidades.

<a id="CP-DOC-00-01-001"></a>
##### CP-DOC-00-01-001 · Contrato DOC-00-01

**Cubre:** DOC-00-01/C-01, DOC-00-01/C-02, DOC-00-01/C-03, DOC-00-01/C-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Catálogo74 HU/219 CA,33seleccionadas/41futuras y 8ideas;60 criterios de encargos y 4J-CA; nombre «Leche», variante « leche », «Léche»; homónimos de personas/proveedores.

1. Validar unicidad de IDs, campos, prioridad, Fibonacci y enlaces HU→CA→caso→evidencia.
2. Comparar vistas07/09/03 con fuente08 y controles de auditoría.
3. Revisar nombre/mínimo de producto y homónimos.

**Resultados esperados:** Cada HU/CA tiene una definición vigente y pruebas escritas con datos/esperado. SP orientativos no equivalen a compromiso del equipo ni horas trabajadas. Producto normalizado duplicado rechaza, acentos se conservan; personas/proveedores homónimos permitidos. No se inventa Sprint/equipo ni se marca verificado por redactar documentación.

<a id="contrato-CT-ROLLBACK-01-POST-ESCRITURA"></a>

### CT-ROLLBACK-01-POST-ESCRITURA · Verificación antes de piloto

**Investigación, no defecto probado.** Preparar entorno PostgreSQL17 aislado (objetivo de diseño), versión menor soportada y registrada; la evidencia18.4 existente sigue útil pero no demuestra17. No migrar ni actualizar el motor operativo en esta fase.

<a id="CT-ROLLBACK-01-POST-ESCRITURA-C-01"></a>

**CT-ROLLBACK-01-POST-ESCRITURA/C-01.** Dada escritura efectiva dentro de transacción aún no confirmada, cuando se termina el proceso servidor propio, entonces tras reconectar no quedan efectos parciales. Registrar barrera después de escritura que demuestre punto exacto de interrupción. Matar una espera anterior a escritura no cubre este caso.

<a id="CT-ROLLBACK-01-POST-ESCRITURA-C-02"></a>

**CT-ROLLBACK-01-POST-ESCRITURA/C-02.** Dado fallo/reinicio del motor aislado, entonces recuperación y reintento preservan unicidad/stock/caja. Distinguir resultado de caída antes/durante/después de commit; si respuesta se pierde tras commit, reintento recupera resultado existente.

<a id="CT-ROLLBACK-01-POST-ESCRITURA-C-03"></a>

**CT-ROLLBACK-01-POST-ESCRITURA/C-03.** Ejecutar E2E actual ADMIN→ALMACENERO→VENDEDOR→ADMIN, permisos cruzados, concurrencia por recursos compartidos, respaldo/restauración verificando integridad, CI real y despliegue seguro. Publicar comandos/versiones/datos/resultados/omisiones y revisión independiente.

**Límites.** Un análisis de código o test Client no acredita navegador, red HTTP real, PostgreSQL17, impresora física, telefonía, lector de pantalla o canal tributario real. Mantener C hasta prueba apropiada. Sin datos del negocio no se certifica normativa ni capacidad operativa. Consultar el corte vigente en ESTADO_GENERAL. La etapa13 tiene cierre acotado al panel mínimo,14 está parcial y15–17 siguen pendientes en primera pasada.

<a id="CP-CT-ROLLBACK-01-POST-ESCRITURA-001"></a>
##### CP-CT-ROLLBACK-01-POST-ESCRITURA-001 · Contrato CT-ROLLBACK-01-POST-ESCRITURA

**Cubre:** CT-ROLLBACK-01-POST-ESCRITURA/C-01, CT-ROLLBACK-01-POST-ESCRITURA/C-02, CT-ROLLBACK-01-POST-ESCRITURA/C-03. **Estado:** EJECUTADO PARCIAL en `05-M` (14/11/2026) solo para `HU-INV-01a` sobre `PostgreSQL 18.4` y HTTP real (`C-01` cierre forzado de proceso HTTP post-escritura en las 4 tablas reteniendo `RowExclusiveLock` y `backend_xid`, `0` residuos y recuperación con reenvío; `C-02` caída inmediata `pg_ctl -m immediate` post-escritura pre-commit conservando durabilidad previa y recuperación con reenvío). Permanecen PENDIENTES en Etapa 15: `PG 17` objetivo, corte físico durante el `COMMIT` del resto de módulos, respaldo/restauración con hashes, pipeline CI, despliegue y `C-03` transversal completo. [Informe 05-M](auditoria_por_etapas/resultados/ETAPA-05.md#reval-05m-20261114)
**Evidencia de ejecución:** [Red HTTP/PG post-escritura 05-M](auditoria_por_etapas/resultados/evidencias/05-J-network-20261115T023959234433Z.json), [PostgreSQL 18.4 05](auditoria_por_etapas/resultados/evidencias/05-postgresql-20261115T023932813038Z.json).
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** Instancia PostgreSQL17 aislada, versión menor registrada; cuentas ficticias; proceso HTTP propio; barrera posterior a escritura efectiva; copia de respaldo con hashes y recuentos.

1. Interrumpir proceso tras escritura y antes de commit; reconectar e inspeccionar todas las tablas.
2. En pruebas separadas, interrumpir/reiniciar motor antes/durante/después del commit y reintentar con misma clave.
3. Ejecutar recorrido navegador ADMIN→ALMACENERO→VENDEDOR→ADMIN, permisos cruzados, concurrencia real, restauración y pipelineCI/despliegue aislado.

**Resultados esperados:** Sin efectos parciales; commit confirmado con respuesta perdida recupera única operación. Respaldo/restauración conserva integridad y balances. Informar versión/comando/barrera/capa HTTP o Client y omisiones. Estado inicial NO EJECUTADO; PG18.4/SQLite previos no demuestran PG17, caída post-escritura ni navegador actual completo.

<a id="CP-INTEGRACION-ROLES-001"></a>
##### CP-INTEGRACION-ROLES-001 · Operación conectada de maestros, existencias, cobro, merma y cierre

**Cubre:** CT-ROLLBACK-01-POST-ESCRITURA/C-03, CT-COHERENCIA-UI/C-01, CT-COHERENCIA-UI/C-02, CT-COHERENCIA-UI/C-03, CT-COHERENCIA-UI/C-04. **Estado:** EJECUTADO en primera pasada14-CIERRE. Cadena y variantes delimitadas comprobadas en Chrome/servidor/persistencia, con revalidación de ajustes, movimientos, merma, dinero y precio. Completa etapa14 para este alcance; los contratos transversales globales y etapas15–17 no se declaran completos.
**Evidencia de ejecución:** Corte vigente14-CIERRE. [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt), [PostgreSQL](auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.
**Evidencia de ejecución:** [Informe14-D](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-d), [44 pasos navegador](auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido3/ejecucion.json), [18 variantes servidor](auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/variantes-despues.json), [versiones finales](auditoria_por_etapas/resultados/evidencias/14-D-20261113/build-final.json).
**Revalidación14-I:** [44 checkpoints nuevos](auditoria_por_etapas/resultados/evidencias/14-I-20261114/navegador/cadena-final/ejecucion.json), mismo caso y datos ficticios, build actual. Se conserva el antecedente14-D; el alcance transversal completo sigue parcial.
**Precondiciones:** Base temporal nueva, tres cuentas ficticias de roles exclusivos y una caja CAJA-01. ADMIN crea categoría, producto y proveedor por interfaz. ALMACENERO registra la primera carga. Cada solicitud conserva su rol y CSRF. Reloj Lima declarado.
**Datos de prueba:** Familia14D y Harina14D, precio3.55, proveedor ficticio con RUC11 ASCII. Lotes A3 y B7, costo2.0000, vencimiento hoy+7 y hoy+30. Venta4, apertura100, efectivo20, merma1 por daño explicado de B. Variante de carga con fecha hoy, categoría desactivada tras preparar borrador, efectivo14.19, merma7 y vencimiento prematuro. Peticiones directas válidas bajo rol incompatible.

1. ADMIN crea categoría, producto y proveedor por menús y contrasta filas persistidas.
2. ALMACENERO carga A3+B7 con proveedor. Rechaza carga vencida sin altas ni costo parcial.
3. VENDEDOR abre100, agrega4 y revisa14.20. ADMIN desactiva categoría mediante confirmación, cobro rechaza y conserva todas las tablas de negocio. ADMIN reactiva.
4. VENDEDOR prueba14.19, corrige a20, confirma y recarga constancia. Contrasta descuento0, base12.03, IGV2.17, vuelto5.80 y lotes A0+B6.
5. ALMACENERO contrasta stock, rechaza merma7 y causa VENCIMIENTO sobre B vigente, registra daño explicado1 y verifica A0+B5.
6. ADMIN abre movimientos, ventas y constancia de la misma operación. Comprueba referencias, autores y total14.20. Inventaría carencias de saldo histórico, filtros y asignación por lote frente a HU-INV-04 y DEC-11-MODELO-AUDITORIA-VENTAS.
7. VENDEDOR cierra114.20, recarga acta y verifica un solo cierre, diferencia0 y bloqueo de preparación con turno cerrado.
8. En variante de servidor separada prueba permisos POST, producto/categoría inactivos, confirmación obsoleta409, vencimiento entre revisión y cobro, robo explicado/sin explicación de vencido, cobro idempotente y cierre repetido. Registra huellas antes/después y control positivo.

**Resultados esperados:** La misma cadena conserva categoría/producto/proveedor, autor de carga, dos lotes, una venta, una merma y un cierre. 10−4−1=5 unidades, apertura100+venta14.20=114.20. Rechazos conservan datos de negocio, estados aprobados se reflejan al siguiente rol y relecturas conservan unicidad. Las superficies con requisitos pendientes quedan PARCIAL o INCUMPLE por criterio. Concurrencia PostgreSQL, caída postwrite, restauración, CI y despliegue conservan pruebas propias en etapa15.

**Revalidación14-F.** La cadena completa de este caso volvió a ejecutarse sobre base nueva y build14-F, con44 checkpoints y maestros creados por formulario. Conservó10−4−1=5 unidades y cierre114.20. La consulta de movimientos mostró las asignaciones reales3/1. [Ejecución nueva](auditoria_por_etapas/resultados/evidencias/14-F-20261113/navegador/cadena-final/ejecucion.json) · [Cobertura y versiones](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f).

El caso se acepta como tarea de verificación por el encargo explícito de etapa14 y CT-COHERENCIA-UI/C-04. Reutiliza HUs/RN/criterios existentes. La aceptación del caso aporta trazabilidad a la auditoría y la tabla de disposiciones registra el fundamento de cada corrección. [Disposiciones14-D](auditoria_por_etapas/resultados/soporte/14-D-disposiciones.md).

<a id="contrato-PROP-E00-HU-02"></a>

### PROP-E00-HU-02 · Ciclo de vida de categorías

Se acepta el siguiente alcance de PROP-E00-HU-02, vinculada al agregado de ciclo de vida de categorías (08, fila QA de HU-CAT-01..02 / HU-PROD-01..04). Como administrador, quiero revisar el efecto de activar o desactivar una categoría antes de confirmarlo para evitar interrumpir por error las operaciones del almacén y las ventas en preparación.

| Criterio suplementario | Dado / cuando / entonces |
|---|---|
| J-CA1. Revisión y cancelación | Dada una categoría existente, cuando ADMIN elige Activar o Desactivar, ve nombre, estado actual, acción y efecto en productos, ventas en preparación e inventario. Abrir, recargar o cancelar conserva el estado. |
| J-CA2. Aplicación y conservación | Dada una revisión vigente, cuando ADMIN confirma, se aplica el destino solicitado. La suspensión bloquea la oferta y las operaciones correspondientes. La reactivación respeta el estado individual y las existencias vigentes. Se conservan lotes, borradores y ventas confirmadas. |
| J-CA3. Pantalla antigua | Dada una lista o confirmación abierta, cuando otro administrador cambia el estado, el siguiente intento desde la versión antigua informa del cambio y pide revisar el estado actual. Incluso si volvió al estado inicial, el envío antiguo se rechaza. |
| J-CA4. Acceso | Dada una cuenta distinta de ADMIN, al intentar revisar o confirmar recibe la respuesta prevista para su rol y el estado se conserva. |

Son criterios adicionales a los 27 CA base del tramo. CAT03 (renombrar) y CAT04 (eliminar) mantienen su clasificación futura. PROD03 fue seleccionado y ampliado en los cortes O/P/Y/Z.

[Auditoría 03-J](auditoria_por_etapas/resultados/anexos/ETAPA-03-J-estado-categoria.md).

<a id="CP-PROP-E00-HU-02-001"></a>
##### CP-PROP-E00-HU-02-001 · Contrato PROP-E00-HU-02

**Cubre:** J-CA1, J-CA2, J-CA3, J-CA4. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.
**Datos de prueba:** ADMINA y ADMINB; categoríaLácteos activa con producto activo e inactivo, lotes y borrador; versiónv1; ALMACENERO/VENDEDOR.

1. Abrir revisión de desactivación, recargar y cancelar.
2. Confirmar revisión vigente.
3. Restaurar; A abrev1, B desactiva/reactiva a v3, A confirma desdev1.
4. Reactivar categoría y consultar productos.
5. Probar roles denegados.

**Resultados esperados:** J-CA1: revisión explica nombre/estado/efecto y cancelar no muta. J-CA2: destino explícito conserva lotes/borradores/ventas; reactivar respeta suspensión individual. J-CA3: versión antigua rechaza incluso tras volver al mismo estado. J-CA4: noADMIN no revisa/confirma; stock/costo/estado intactos.

<a id="contrato-CT-COHERENCIA-UI"></a>

## CT-COHERENCIA-UI · Toda promesa visible es auditable

Requisito ACEPTADO por instrucción expresa del usuario. Aplica a las páginas y estados alcanzables, mensajes, etiquetas, tablas, ayudas, botones, menús, impresión y resultados que pueda leer cada rol. Una frase equivocada se corrige junto con su comportamiento según el requisito aceptado. Si no existe requisito, se registra extra o contradicción y se define su tratamiento; no se toma el texto implementado como aprobación comercial.

<a id="CT-COHERENCIA-UI-C-01"></a>

**CT-COHERENCIA-UI/C-01.** Dada la superficie y los estados descritos en CP-VISIBLE-001, cuando se revisan desde cada rol, entonces ningún éxito antes de commit ni error con mutación oculta; mensaje precisa causa y acción posible. Extra sin requisito se registra para decisión, sin aceptarlo por estar implementado. No se rebaja el requisito para hacer coincidir un bug.

<a id="CP-VISIBLE-001"></a>
##### CP-VISIBLE-001 · Promesa de operación y resultado real

**Cubre:** CT-COHERENCIA-UI/C-01. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Build identificado; datos ficticios aislados; inventario por rol, ruta y estado.
**Datos de prueba:** Una fila por cada texto de éxito, error, ayuda, botón, enlace, estado, etiqueta e impresión; registrar literal, ruta, rol y estado de datos. Ejemplo: recepción «registrada» con lote inválido.

1. Inventariar plantillas, textos dinámicos y respuestas del servidor; recorrerlos en navegador con cada rol.
2. Enlazar cada promesa con HU/RN/CA; provocar éxito, rechazo y fallo de red.
3. Comparar mensaje con respuesta, persistencia y lo que ve el siguiente rol.

**Resultados esperados:** Ningún éxito antes de commit ni error con mutación oculta; mensaje precisa causa y acción posible. Extra sin requisito se registra para decisión, sin aceptarlo por estar implementado. No se rebaja el requisito para hacer coincidir un bug.

<a id="CT-COHERENCIA-UI-C-02"></a>

**CT-COHERENCIA-UI/C-02.** Dada la superficie y los estados descritos en CP-VISIBLE-002, cuando se revisan desde cada rol, entonces unidades y conceptos explícitos; físico no se llama vendible; total filtrado no es total de página. No afirmar «sin productos» cuando hay un fallo de consulta. Mensajes/estados obsoletos exigen revisión sin cobro silencioso.

<a id="CP-VISIBLE-002"></a>
##### CP-VISIBLE-002 · Cantidades, dinero, filtros y estado comercial

**Cubre:** CT-COHERENCIA-UI/C-02. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Build identificado; datos ficticios aislados; inventario por rol, ruta y estado.
**Datos de prueba:** Leche18físico/10vendible; vencidos/inactivos; venta20/base16.95/IGV3.05; filtrosvacíos e inválidos;26filas.

1. Comparar cada contador, total, alerta y etiqueta con consulta autorizada a datos de prueba.
2. Cambiar filtros, página, fechaLima y estado del producto desde otra sesión.
3. Revisar rótulos y contenido en pantalla e impresión.

**Resultados esperados:** Unidades y conceptos explícitos; físico no se llama vendible; total filtrado no es total de página. No afirmar «sin productos» cuando hay un fallo de consulta. Mensajes/estados obsoletos exigen revisión sin cobro silencioso.

<a id="CT-COHERENCIA-UI-C-03"></a>

**CT-COHERENCIA-UI/C-03.** Dada la superficie y los estados descritos en CP-VISIBLE-003, cuando se revisan desde cada rol, entonces menú y autorización coinciden; no anuncia operación disponible que termina sistemáticamente denegada. Función futura se etiqueta y no ofrece acción engañosa. Constancia interna no simula boleta/factura ni validación SUNAT. La ayuda describe el lector y la confirmación realmente implementados.

<a id="CP-VISIBLE-003"></a>
##### CP-VISIBLE-003 · Permisos, navegación y disponibilidad anunciada

**Cubre:** CT-COHERENCIA-UI/C-03. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Build identificado; datos ficticios aislados; inventario por rol, ruta y estado.
**Datos de prueba:** ADMIN/ALMACENERO/A/B/visitante/revocado; pantallas vacías, cargadas, bloqueadas y error; móvil390×844 y escritorio.

1. Recorrer menús, enlaces de retorno, acciones por teclado y URLs directas.
2. Cambiar de rol/cuenta y probar ID ajeno, cookie vieja y pestaña antigua.
3. Revisar enlaces de funciones futuras, canal fiscal y ayudas de lector.

**Resultados esperados:** Menú y autorización coinciden; no anuncia operación disponible que termina sistemáticamente denegada. Función futura se etiqueta y no ofrece acción engañosa. Constancia interna no simula boleta/factura ni validación SUNAT. La ayuda describe el lector y la confirmación realmente implementados.

<a id="CT-COHERENCIA-UI-C-04"></a>

**CT-COHERENCIA-UI/C-04.** Dada la superficie y los estados descritos en CP-VISIBLE-004, cuando se revisan desde cada rol, entonces se distingue CUMPLE/INCUMPLE/PARCIAL/NO EJECUTADO/NO EXAMINADO/FUTURO/EXTRA SIN REQUISITO/CONFLICTO. Una lista de plantillas o una suite verde no equivale a cobertura visual completa. El inventario sin recorrer permanece pendiente, nunca se marca verificado por inferencia.

<a id="CP-VISIBLE-004"></a>
##### CP-VISIBLE-004 · Registro completo de cobertura inversa

**Cubre:** CT-COHERENCIA-UI/C-04. **Estado:** DISEÑADO — NO EJECUTADO en este corte.
**Precondiciones:** Build identificado; datos ficticios aislados; inventario por rol, ruta y estado.
**Datos de prueba:** Inventario con identificador literal estable, build/hash, rol, ruta/estado, requisito, caso, evidencia y observado; excluir solo con motivo explícito.

1. Conciliar inventario estático con recorrido dinámico por roles; incluir textos condicionales.
2. Buscar elementos sin requisito o sin prueba y abrir hallazgo trazable.
3. Revisar ausencia de pendientes en cada tramo antes de declarar cobertura de ese tramo.

**Resultados esperados:** Se distingue CUMPLE/INCUMPLE/PARCIAL/NO EJECUTADO/NO EXAMINADO/FUTURO/EXTRA SIN REQUISITO/CONFLICTO. Una lista de plantillas o una suite verde no equivale a cobertura visual completa. El inventario sin recorrer permanece pendiente, nunca se marca verificado por inferencia.

<a id="fuera"></a>

## Ideas excluidas y asuntos que requieren refinamiento

Estas ocho ideas no forman parte de las historias activas de la bodega y no tienen criterios de aceptación detallados ni puntaje asignado. Se registran para dejar constancia de las decisiones tomadas:

| ID | Nombre de la idea | Motivo de exclusión |
|---|---|---|
| `HU-CLI-01` | Clientes — Listar clientes registrados | Excede la venta directa en mostrador a público general de la bodega. |
| `HU-CLI-02` | Clientes — Captura y reconocimiento de clientes en ventas nominales | La identificación fiscal con DNI o RUC corresponde a la facturación electrónica futura fuera del alcance académico. |
| `HU-CLI-03` | Clientes — Editar correo electrónico de cliente | Vinculado a la gestión de clientes nominales, función fuera de alcance. |
| `HU-VEN-02b` | Ventas — Emitir boleta nominal de más de S/ 700.00 | Emisión fiscal fuera del sistema actual; canal real y aplicabilidad por confirmar. El título histórico no establece un umbral tributario vigente. |
| `HU-VEN-02c` | Ventas — Emitir factura comercial con RUC | Emisión fiscal fuera del sistema actual; canal real y aplicabilidad deben confirmarse antes del piloto. |
| `HU-VEN-03` | Ventas – Generar comprobante en PDF o reenviar por correo | El despacho digital de comprobantes fiscales queda supeditado a la facturación tributaria futura fuera de alcance. |
| `HU-VEN-08` | Ventas — Exportar historial de ventas a PDF | Las consultas de ventas se realizan directamente en pantalla; la exportación de gestión permanece futura en HU-REP-09. |
| `HU-VEN-09` | Ventas — Registrar venta a granel o por peso | El alcance de esta versión admite productos envasados por unidad con código de barras; no afirma que esa sea toda la actividad real del negocio. |

Las ocho ideas son W, sin puntos ni casos operativos comprometidos: no constituyen HU listas para desarrollo. Conservar sus IDs no exige inventar estimaciones o cumplimiento. AUTH05 (seguridad del código), CAJA07 (borradores/arqueo), VEN06 (devolución/reembolso), DASH01 (latencia de actualización) y REP07 (base comparable del costo) requieren refinamiento específico; sus casos son especificación futura acotada, no una certificación de preparación.

## Evidencia, discrepancias y siguiente trabajo

El [mapa consolidado](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) conserva clasificación A/B/C/D/E, prioridad, estado, fuente y dependencias; el [índice de IDs](auditoria_por_etapas/resultados/conciliacion_20261112/INDICE_IDS.md) mantiene trazabilidad histórica. La [conciliación de este corte](auditoria_por_etapas/resultados/fuente_unica_20261112/REVISION.md) registra cambios y límites. Las divergencias comprobadas de promedio, recepción, merma y modelo de venta siguen abiertas hasta implementación y verificación. No se declara cerrado ningún módulo.

## Técnicas de planificación

MoSCoW y Fibonacci son técnicas elegidas para este proyecto, no mandatos de Scrum. [Agile Business Consortium: MoSCoW](https://www.agilebusiness.org/resource/what-is-moscow-prioritization/) define prioridades respecto a un horizonte; [Scrum Guide](https://scrumguides.org/scrum-guide.html) atribuye el dimensionamiento a quienes realizan el trabajo. Por eso estas cifras son orientativas hasta refinamiento con el equipo.

La dependencia de valoración del caso CP-INTEGRACION-ROLES-001 se revalidó separadamente con F-COSTO en14-E, contra su propio build. [Recorrido y límites14-E](auditoria_por_etapas/resultados/evidencias/14-E-20261113/navegador/RESUMEN.md). La evidencia14-D de creación de maestros y sus variantes se conserva como heredada.
