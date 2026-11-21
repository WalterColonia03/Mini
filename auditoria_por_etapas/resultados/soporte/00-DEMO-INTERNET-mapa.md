# Línea base del cambio DEMO-INTERNET · 15/11/2026

**Sublote:** `00-DEMO-INTERNET-BASELINE-01`. **Pasada:** actualización preparatoria del inventario; no segunda pasada funcional. **Resultado:** inventario estático y mapa de dependencias preparados; no aprobación funcional, monetaria ni pública. La revisión de los 18 prompts es un corte anterior separado.

## Versión, alcance y reproducción

- Fuente08 SHA256: `600566eaab6729c5e18cff2e3df2c6202cb319e89140d83062217e30f3df7361`.
- HEAD de aplicación: `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, con cambios locales preexistentes; HEAD por sí solo no identifica el producto.
- Las 221 fuentes del manifiesto01-K se volvieron a comparar y no cambiaron. Conservan su build `8c154de8b9b4446b20c024c5e6e32269d66b63d120eaab088440ed5639ef392d`. Se comprobaron además los 267 archivos protegidos del corte documental: cero cambios.
- Base principal SHA256: `83e79733798e2e00af2b8f11b7a23aac2b1727d16707d078873d5a36d441bb6c`; solo se leyó para obtener su huella. No se abrió conexión de base, servidor ni navegador.
- Comando desde la raíz: `python auditoria_por_etapas/resultados/soporte/inventariar_00_demo.py`. Analiza AST y Markdown, no importa Django ni lee `.env`.

[Manifiesto y resultados](../evidencias/00-DEMO-INTERNET-20261115/linea-base.json) · [Requisitos y casos](../evidencias/00-DEMO-INTERNET-20261115/requisitos.json) · [Superficies](../evidencias/00-DEMO-INTERNET-20261115/superficies.json) · [Fallos heredados](../evidencias/00-DEMO-INTERNET-20261115/fallos-heredados.json).

## Inventario revalidado estáticamente

08 contiene 75 HU: 35 seleccionadas, 40 futuras y 8 ideas excluidas adicionales. Se inventariaron 301 criterios y 121 CP escritos. Los estados de ejecución copiados desde08 conservan su evidencia histórica; no son ejecuciones de este sublote. Los derivados07/09/03 coinciden con el generador.

En las fuentes comparadas se localizaron 47 rutas finales declaradas y 5 inclusiones, 44 plantillas, 84 clases declaradas en archivos de modelos/formularios, 267 asignaciones directas a campos u otros atributos de clase, 129 funciones de vistas/servicios/autorización/middleware, 548 métodos `test_*` y 239 llamadas candidatas a mensajes/validaciones. Estos recuentos son localizaciones de código, no pantallas, campos efectivos, CP ejecutados ni criterios aprobados. No expanden campos heredados, variantes dinámicas ni tests parametrizados. El inventario completo de cada superficie se profundiza en su etapa.

`config/urls.py` ya no publica `/admin/`; `sales/urls.py` mantiene ocho rutas de efectivo/borrador/historial sin endpoints de Yape, mixtos o reintegros. `Sale` conserva `cash_received`/`change_given`; la constancia escribe «Efectivo». Estas observaciones revalidan la existencia del código, no el comportamiento HTTP. El hallazgo histórico15-A sobre admin publicado no debe copiarse como defecto actual sin comprobar el build; tampoco se atribuye al inventario una nueva prueba de404.

## Selección y dependencias para la nueva entrega

| Tramo | Requisitos / acciones | Estado del nuevo objetivo | Evidencia que falta |
|---|---|---|---|
|01 ingreso y barreras | HU-AUTH-01/02, RN-17 | Cierre local01-K HEREDADO, acotado a sus siete CA | Revalidación pública del build candidato; no reabrirlo por pagos ajenos sin dependencia |
|02 empleados y salida | HU-AUTH-03, HU-USR-01..05, DOC-02-04; roles y revocación | Próximo sublote; evidencia02-E HEREDADA y contratos por contrastar | Literales, permisos directos, sesiones antiguas y carreras; amenaza de empleado con turno abierto |
|03–08 inventario | Maestros, carga/recepción, stock, lotes, mermas/ajustes | Conserva resultados y defectos propios | Efectos del pago tardío, cambio de precio/stock y devolución física cuando se implemente el nuevo flujo |
|09 caja | HU-CAJA-01/02/05, RN-08/10/30 | Efectivo existente; nuevo desglose no revalidado | Componentes por medio, devolución autorizada, cierre conservado y empate temporal |
|10 preparación | HU-VEN-01b, RN-27/29/30 | Borrador existente; abonos todavía ausentes | Conservar dinero si se descarta/sale; orden de captura y cambio de precio/stock |
|11 cobro | HU-VEN-01c, HU-VEN-07 seleccionada, HU-VEN-10 nueva, RN-02 | Yape/mixto seleccionados, NO IMPLEMENTADOS por este trabajo | Canal legítimo, referencia real, literales, persistencia, concurrencia y recuperación |
|12 constancias/historial/reintegro | HU-VEN-02a/05a/05b y06a/b/c; CT-ENTREGA-ACADEMICA/C-04 | Anulación/reintegro son dependencias obligatorias por refinar, no capacidad disponible | Medio, delegación, cancelación antes/después del abono, devolución de mercadería y desglose |
|13–14 consultas/integración | Componentes en indicadores, cadena por roles | Evidencia anterior no incluye pagos nuevos | No duplicar ventas/dinero; casos simultáneos y dueño ausente |
|15 publicación y seguridad | CT-ENTREGA-ACADEMICA/C-01/03/05 | URL/proveedor no seleccionados; NO DESPLEGADO | HTTPS externo, persistencia, restauración, permisos, carreras y tiempos medidos |
|16 factibilidad | Caso100 Inca Kola3L, comprobante meses después; condiciones del medio de pago | Pendiente, sin certificación fiscal ni legal | Fuente SUNAT vigente, diferencia factura/constancia, canal de pago y costo reales |
|17 entrega | CT-ENTREGA-ACADEMICA completo | NO EJECUTADA | Todos los criterios seleccionados con evidencia pública del mismo build |

HU-VEN-07 aporta nueve CA; HU-VEN-10, cinco; el contrato de entrega, seis. Sus nuevos CP siguen diseñados. No existe todavía un catálogo final aceptado de todos los literales de estas superficies; debe definirse en08/CA/CP antes de implementar. HU-VEN-07 conserva denominación «código de operación»: su formato y disponibilidad son hechos externos por verificar, no autorización de inventar un identificador o tratar tres dígitos como únicos.

## Mapa inicial de Etapa02

| Ruta | Permiso/método declarado por inspección | Acción |
|---|---|---|
|`/empleados/`|ADMIN activo, GET|Listar/buscar empleados|
|`/empleados/nuevo/`|ADMIN activo, GET/POST|Alta con nombre/correo/clave/rol|
|`/empleados/<uuid>/editar/`|ADMIN activo, GET/POST|Editar cuenta, cambio de rol/clave y desbloqueo explícito|
|`/empleados/<uuid>/estado/confirmar/`|ADMIN activo, GET|Confirmación sin mutación|
|`/empleados/<uuid>/estado/`|ADMIN activo, POST|Desactivar/reactivar con acción explícita|
|`/salir/`|Sesión autenticada, GET/POST|Confirmar salida; descartar borrador y revocar sesión actual|

Referencias: `identity/views.py:90,145,172,230,309,358`; `identity/authorization.py:19`; `identity/middleware.py:24`. Las referencias identifican el build arriba citado. El servicio vuelve a comprobar el actor bajo bloqueo; el middleware controla sesiones rechazadas. Se trata de inspección, no de acceso denegado demostrado en esta sesión.

### Propuestas y riesgos que debe resolver02

| ID / hallazgo | Recomendación y alternativas | Beneficio / riesgo / costo / impacto |
|---|---|---|
|PROP-02-REVOCACION-TURNO-01|Separar suspensión de acceso y resolución del turno. Actualmente `identity/services.py:331,462` prohíbe cambio de rol/desactivación con turno abierto. Los CP de08 también lo esperan. Evaluar suspensión conservando dinero/turno y resolución por permiso delegado, frente a mantener la regla anterior|Puede detener a empleado sospechoso sin su cooperación. Costo medio/alto y nueva política/HU/CA/CP antes de implementar; impacta02/09/10/14. No cerrar ni apropiarse de caja automáticamente. Es brecha operativa, no bug demostrado contra el contrato anterior|
|PROP-02-DELEGACION-LIMITADA-01|Definir permisos de solicitar, autorizar y ejecutar un reintegro, separados de editar empleados/QR. No promover al cajero aADMIN para resolver la ausencia del dueño|Reduce concentración de poder; costo medio según política. No crear cuarto rol ni privilegios por silencio; impacta02/11/12/14|
|REV-02-SESIONES-01|Revalidar desactivación, cambio de clave/rol y reactivación con dos navegadores, cookie antigua y POST preparado; carreras contra cobro/caja|Evita operaciones tras revocación; costo de pruebas medio, requiere PostgreSQL y datos aislados. Existencia de tests secuenciales no aprueba carreras|
|REV-02-POST-01|Intentar UUID ajeno, rolADMIN, desbloqueo y campos no permitidos desde vendedor/almacenero con CSRF válido; verificar rechazo sin mutación|Control de escalada real, costo bajo/medio. Revalidar servicio y ruta, no solo menú|
|REV-02-SALIDA-01|Probar salida desde sesiónA y continuidad de sesiónB de la misma cuenta; conservar turno y explicar efecto del descarte del borrador. Añadir abonos persistentes cuando existan|Evita pérdida/confusión al salir; costo medio. La actual salida descarta borrador del actor, no solo de la pestaña|
|REV-02-SESIONES-VOLUMEN-01|Medir borrado/sincronización de sesiones con volumen aislado: el servicio recorre todas las sesiones (`identity/services.py:217,233`)|Puede afectar rapidez de revocación; costo bajo de medición. No hay lentitud demostrada ni razón para imponer un nuevo límite arbitrario|

Estas propuestas no cambian automáticamente el contrato ni los permisos del producto. Se conserva la separación de etapas01 y02.

## Hechos externos y trabajo independiente

`PAY-CANAL-01`: Ayudantes es propuesta oficial de consulta humana con costo, no API contratada. Falta decisión del usuario, elegibilidad de la cuenta receptora, referencia disponible y prueba humana pequeña acordada. El perfil bancario Ayudante no concede rolADMIN en la aplicación. La alternativa con confirmación independiente necesita canal autenticado real; no se reemplaza con captura, sonido, notificación leída ni referencia inventada.

`PAY-REINTEGRO-01`: queda prohibido el nuevo yapeo. Se recomienda evaluar reintegro en efectivo con permiso delegado, deuda y recepción verificadas, límite acumulado y salida trazable; método y atribuciones todavía no aceptados. Solicitar, autorizar y entregar dinero son hechos separados. El dueño no debe aprobar cada operación. El sistema puede controlar registros y permisos; por sí solo no demuestra que el efectivo físico fue entregado ni impide colusión.

`DEMO-ALOJAMIENTO-01`: no hay URL/proveedor elegidos. Puede usarse subdominio de un servicio compatible; no requiere comprar dominio. Publicar está pendiente y no se confunde con tener Docker o una prueba local. No hay afiliación ni gasto autorizado por este informe.

En paralelo pueden continuar02 y defectos existentes de03–10; inventario de literales, pruebas deterministas, permisos y preparación de despliegue. No habilitar cobro real hasta disponer de sus hechos externos imprescindibles.

## Fallos heredados y límites

Conservar los tres tests fallidos de01-K: orden de turnos (`cash.test_audit09_cash...test_shift_history_isolation_styles_and_constant_query_count`), desempateFEFO (`inventory.test_audit14g_receipts...test_sale_fefo_keeps_two_receipt_origins_and_average_snapshot`) y orden de líneas (`sales.test_audit12_receipts_history...test_receipt_line_order_three_items_reversed_uuids_and_legacy_fallback`). El triage identifica fragilidad temporal en los dos primeros y exigencia de orden de captura por resolver en el tercero; no se reejecutaron ni arreglaron aquí. Los IDs completos y fuente quedan en el JSON.

**Cobertura de este sublote:** versión y artefactos revalidados por lectura; 301 criterios inventariados, cero criterios funcionales reejecutados; cero navegador, transferencias o pruebas públicas. Se preservan snapshots anteriores. No se aprueba02 ni la entrega.

**Cursor siguiente:** `02-DEMO-TRAZABILIDAD-01`, comenzando con inventario de HU-AUTH-03 y HU-USR-01..05, literales y permisos vigentes, antes de elegir un sublote funcional. Decisiones paralelas `PAY-CANAL-01`, `PAY-REINTEGRO-01` y propuesta `PROP-02-REVOCACION-TURNO-01`.
