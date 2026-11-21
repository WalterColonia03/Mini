# Registro de decisiones y encargos verificables · 12/11/2026

## Cómo usar este registro

Complementa el [mapa](CONSOLIDACION.md), que registra ID, clasificación, prioridad, fuente y dependencia. Las decisiones nuevas están **ACEPTADAS por delegación explícita del usuario en esta conversación**, con fecha de este corte. La implementación de los cambios descritos está **PENDIENTE DE AUTORIZACIÓN SEPARADA**. La existencia de código parecido o pruebas antiguas no cambia ese estado. Las políticas ya implementadas conservan únicamente la evidencia acotada de su informe de origen.

Los IDs de apartado son originales. Los criterios nuevos tienen identidad compuesta `ID-del-apartado/C-nn`; no sustituyen `HU-xxx/CA-nn` ni reutilizan ordinales de la antigua tabla QA. Cada contrato se aplica además con las condiciones comunes siguientes. Justificación/alternativas/costo relativo están en el mapa y, para los riesgos principales, en estos apartados.

## Condiciones comunes para todos los cambios seleccionados

- Confirmar rol activo y permiso en servidor; validar nuevamente dentro de la transacción los actores/entidades que compiten. Un menú oculto no autoriza una petición. Visitante no es un cuarto rol.
- Entradas inválidas, estado omitido, UUID ajeno, CSRF inválido, usuario revocado, doble envío divergente y límites excedidos deben producir un error comprensible sin efectos parciales en stock, costo, lotes, venta, correlativo, turno ni efectivo. Verificar el conjunto completo de datos antes/después; un HTTP400/403 no basta.
- Las escrituras se hacen por POST. GET es consulta. Usar orden de locks común, documentado a partir de todos los servicios implicados, y pruebas de carrera real en PostgreSQL con conexiones independientes/barrera que demuestre solapamiento. Registrar cuándo se usa Django Client, HTTP por sockets o navegador real; no intercambiar esos nombres.
- Registrar migración/diagnóstico de datos, reversibilidad y backup/restauración en un clon. Nunca fusionar, borrar, completar ni revalorar datos operativos por inferencia. Costos históricos desconocidos quedan desconocidos y los reportes indican cobertura.
- Actualizar HU/RN afectadas, este registro, backlog, matriz y evidencia en la misma entrega. Verificación: unitarias de cálculo/forma, integración de transacción, permisos, concurrencia cuando hay recursos compartidos, navegador para comportamiento visible y regresión integral. La DoD exige el alcance completo acordado, no solo tests verdes.
- Mensajes específicos pueden adaptar el estilo visual, pero deben comunicar causa y siguiente acción sin revelar secretos. Nunca guardar contraseñas, cookies, CSRF, tokens ni cuerpos completos sensibles en logs. Datos de prueba ficticios, base nueva y hashes del producto/base operativa antes y después.

## DOC-03AB-01 · Entrada directa de almacén

**Decisión/justificación.** Mantener la recepción ordinaria directa por ALMACENERO, para no imponer un circuito SOL completo al minimarket. ADMIN autoriza compras mediante el procedimiento externo del negocio; el sistema registra recepción, no acredita aprobación externa. Esta política tiene costo relativo bajo-medio; SOL completo queda futuro. Cambiaría si la operación real requiere autorización previa trazable por importe o comprador.

**Alcance.** RN-01, HU-INV-01b, HU-SOL-01..05b, backlog/diseño/matriz. Producto y categoría activos; carga inicial confirmada; proveedor activo opcional, con etiqueta «Sin proveedor asignado» si falta. No suponer RUC ni proveedor inexistentes. Si el negocio adopta proveedor obligatorio se necesita cambio posterior explícito, no una falsa obligación fiscal.

**C-01.** Dado un producto habilitado y su carga inicial, cuando ALMACENERO confirma una recepción válida, entonces se registra con identidad propia, autor, instante Lima/UTC, lotes, cantidades y costos, sin exigir solicitud SOL.

**C-02.** Dada una solicitud inexistente o futura, cuando se consulta la recepción actual, entonces no se presenta como «solicitud aprobada». ADMIN/VENDEDOR no reciben permiso de escritura de almacén por conocer la URL.

**Migración/excepciones.** Ningún cambio de stock por documentar la excepción. Recepciones antiguas conservan origen conocido; no fabricar aprobaciones. Depende de DOC-03AI-01/03AH-01 antes de considerar completa la recepción.

## DOC-03AH-01 · Promedio móvil coherente

**Decisión.** Promedio ponderado sobre existencia física registrada, incluyendo vencidos pendientes de baja. Venta/baja/ajuste negativo conserva costo unitario promedio; al quedar stock físico total cero, promedio vigente=0. Expirar no modifica stock físico ni promedio: impide venta. Esto separa disponibilidad y valoración interna. No constituye método fiscal certificado ni valoración al menor entre costo y valor realizable.

**Entradas y cálculo.** Decimales, precisión4, HALF_UP. Entrada: `(Q×C + q×c)/(Q+q)`, con Q físico y C promedio anterior bloqueados; carga inicial pondera todas sus líneas. Ajuste positivo por conteo con Q>0 usa el promedio vigente para las unidades encontradas, no inventa compra; con Q=0 exige costo positivo documentado y fuente/motivo explícitos. Si falta costo fiable se rechaza y se requiere investigar, sin permitir venta de existencia no regularizada. Una recepción real usa su costo de adquisición declarado, no el costo del ajuste.

**C-01.** Dadas18 unidades registradas con promedio3 (8 vencidas,10 vendibles), cuando llegan10 a6, entonces Q=28, vendible20 y C=4.0714. La fecha de vencimiento sola no altera C.

**C-02.** Dado stock con promedio4.0714, cuando se vende/dá de baja una unidad, entonces la salida conserva ese costo histórico y C sigue4.0714 si queda stock; si queda cero, C=0 sin alterar snapshots previos.

**C-03.** Dado un ajuste positivo con Q>0, cuando se confirma, entonces aumenta Q al promedio vigente y conserva su procedencia como ajuste. Con Q=0 y costo ausente, rechaza sin mutación.

**C-04.** Dadas recepción y venta/baja concurrentes, cuando se solapan, entonces cada resultado equivale a uno de los órdenes seriales válidos; ninguna pierde cantidades ni usa un promedio a medio actualizar. Con fallo posterior a escritura, rollback total.

**Datos.** Diagnosticar historia y corte de valoración antes de cambiar algoritmo. No retrocalcular `SaleLine.unit_cost=NULL` con promedio actual ni reescribir ventas conocidas. Si no hay historia suficiente, preparar ajuste de apertura de valoración explícito, documentado y autorizado antes de aplicarlo. Afecta RN-14/28, INV01a/01b/02/03, VEN01c y REP07 futuro. La prueba antigua que exige recalcular por costos de lotes restantes se sustituye con trazabilidad; no se elimina simplemente para obtener verde.

## DOC-03AI-01 · Recepción propia e idempotente

**Decisión.** Una recepción confirmada por producto y uno o varios lotes tiene UUID, referencia visible `R-00000001`, responsable, instante y contenido inmutable. El correlativo de recepción es global del minimarket, ascendente, único, de ocho dígitos, sin reinicio por producto/fecha/turno ni reutilización de números confirmados. Se reserva bajo lock dentro de la misma transacción; rollback no deja recepción parcial. Al agotarse99,999,999 se rechaza antes de mutar, con mensaje de capacidad y revisión administrativa, sin truncar o reiniciar. Carga inicial sigue siendo única y conserva su constancia. Recepción multiproducto y solicitudes se difieren. Costo medio: hay cambio de persistencia y migración.

**Modelo recomendado.** Identificar cada ingreso físico de lote por su recepción; conservar número comercial normalizado y vencimiento. Permitir que un mismo lote comercial llegue en recepciones distintas sin mezclar fecha/costo/proveedor/origen. Eliminar la unicidad global `(producto,número)` solamente al reemplazarla por integridad de recepción y comprobar colisiones. Dentro de una recepción, un mismo número/vencimiento no aparece duplicado: rechazar o consolidar antes de confirmar con vista explícita, nunca sumar silenciosamente en reintento. Para mismo número comercial con vencimiento contradictorio, rechazar hasta aclaración documentada. FEFO mantiene vencimiento→ingreso→ID inmutable. No imponer cinco tablas si una estructura menor preserva esas garantías.

**C-01.** Dada clave UUID nueva y entrada válida, cuando se confirma, entonces stock/costo/recepción/lotes/autor/correlativo se guardan en una transacción y se devuelve su constancia.

**C-02.** Dada una clave confirmada y el mismo actor/contenido, cuando se repite incluso tras perder la respuesta, entonces se devuelve exactamente la recepción anterior sin nuevos efectos. Distinto contenido/actor no obtiene datos ajenos y rechaza sin mutación. La huella usa valores normalizados, no el orden incidental del HTML.

**C-03.** Dado otro ingreso real del mismo lote comercial, cuando usa una clave nueva y datos coherentes, entonces se crea otra recepción conservando ambas procedencias. Dos conexiones con la misma clave producen una sola confirmación.

**C-04.** Dada una entrada inválida, cuando se corrige antes de confirmar, entonces no queda clave consumida como éxito ni lote/stock parcial. No confundir duplicado comercial con reintento técnico.

**Datos existentes.** La FK a `InitialInventoryLoad` no prueba que cada lote pertenezca a la primera carga. Migrar solo información demostrable; separar legado con origen incompleto y enlazar evidencias, sin inventar una factura, recepción multiproducto o correlación temporal. Cargas/entradas y snapshots conservan proveedor/autor originales aunque después se editen. RN01/14/19, INV01a/b/04, PROV01/04.

La cantidad recibida en una constancia es inmutable. Un ajuste positivo no modifica esa fotografía aunque el campo técnico actual `Lot.initial_quantity` aumente para admitir más saldo. Separar cantidad original recibida y movimientos posteriores; no usar una capacidad mutable como cantidad histórica de recepción.

## DEC-11-MODELO-AUDITORIA-VENTAS · Venta, lotes, caja e historia

**Requisito existente.** RN-25 exige asignaciones de lote; diseño §2.5 exige snapshots vendedor/caja. El código descuenta lotes y conserva producto/precio/costo, pero no persiste las asignaciones ni esos dos snapshots. Es trabajo técnico, no decisión sobre si conviene cumplirlo.

**Diseño recomendado.** `SaleLotAllocation` por línea/lote y cantidad positiva; suma por línea=cantidad vendida. Añadir posición estable por línea y snapshots de nombre del vendedor/código de caja a la venta. Garantías de `inventory_movement`, `cash_movement`, `audit_event` e idempotencia se implementan de forma explícita o mediante equivalencia documentada y probada; retener `SaleDraftLine` no satisface trazabilidad de lotes. Para el tamaño del proyecto son adecuados movimientos append-only y vínculo único de movimiento de efectivo con venta, sin microservicios. Una clave/huella en la entidad confirmada puede satisfacer idempotencia sin tabla genérica adicional.

**C-01.** Dada venta de5 unidades con lotes3+2 elegibles, cuando confirma, entonces persisten dos asignaciones3/2, un movimiento efectivo por total, snapshots, costo, correlativo y descuento stock, atómicamente; sumaasignada=5.

**C-02.** Dado fallo al insertar cualquiera de esos elementos, cuando se revierte, entonces todas las tablas, contador y stock quedan como antes. Doble POST devuelve la misma venta.

**C-03.** Dados cambios posteriores de nombre, código, vendedor o caja, cuando se consulta constancia, entonces refleja la fotografía original y no el dato maestro actual; no muestra costos.

**C-04.** Dado legado sin asignaciones/snapshot/costo, cuando se consulta historia o margen, entonces identifica dato no disponible y no lo atribuye a un lote por aplicar FEFO al stock actual. Un backfill solo usa evidencia inequívoca y guarda procedencia.

Afecta VEN01c/02a/05a/05b, INV04, RN19/25/26/28 y diseño DB. La migración de costo histórico es `sales.0005`, no `sales.0004` (esta última añade producto).

**PROP-11-05 — Borrador después del cobro.** Se conserva temporalmente el comportamiento de retener líneas del borrador cobrado como soporte técnico, sin considerarlas historia canónica de venta ni asignaciones de lote. No se borran datos antiguos ni se crea un archivo adicional por iniciativa del implementador. La política de eliminación/retención se resuelve con SEC-15-RETENCION-01; las consultas usan Sale/SaleLine/snapshots/asignaciones. Dado un cobro confirmado, cuando se consulta historial, entonces no depende de que el borrador siga disponible ni permite volverlo a cobrar. Salir con borrador no cobrado conserva la regla específica de descarte de RN-30.

## DEC-11-DESCUENTOS-ALCANCE · Nuevos cobros sin descuento discrecional

**Decisión/alternativas.** Se suspende el descuento libre nuevo hasta definir política concreta de promoción/autorización. Es más sencillo y evita entregar dinero al criterio de cualquier vendedor. Conservar el descuento libre tiene menor costo inmediato y riesgo comercial; construir aprobación con porcentajes arbitrarios añade complejidad injustificada. No inventar un máximo5/10/20% ni pedir contraseña compartida de ADMIN.

**C-01.** Dado un cobro nuevo, cuando el vendedor llega a confirmación, entonces no puede introducir descuento; el servidor solo admite descuento cero/ausente con semántica cero. Un importe positivo, negativo, inválido o manipulado se rechaza con «Los descuentos no están habilitados para nuevas ventas» sin mutación.

**C-02.** Dada venta histórica con descuento, cuando se consulta o se reintenta idempotentemente la confirmación ya realizada, entonces conserva importes/constancia anteriores, sin recalcularla a cero ni crear otra venta. La comprobación de identidad de reintento precede la aplicación de política de venta nueva.

**C-03.** Dada una nueva venta, entonces subtotal=total antes de cálculo interno base/IGV según RN27, y caja recibe total. Mantener campos históricos y reportes no habilita nuevas promociones.

Afecta VEN01b/01c/02a/05a/b, RN25/27, forms/services/templates/JS/tests. HU-VEN-03 sigue PDF/correo fuera de alcance; propuestas de HU descuento se archivan como futuro, no se reutiliza ese ID. Sin migración destructiva.

## DEC-12-PERMISOS-HISTORIAL-Y-MENU · Permisos comerciales

**Decisión.** ADMIN administra personal/catálogo/proveedores, realiza ajustes y bajas, consulta stock, cargas/recepciones/bajas/movimientos y toda venta/turno. ALMACENERO registra cargas/recepciones/bajas y consulta inventario/proveedores/catálogo necesarios, sin operar caja/ventas. VENDEDOR abre/prepara/cobra/cierra su turno, consulta sus propias ventas/turnos/constancias y productos vendibles en POS. Ninguno obtiene permisos técnicos por su rol comercial. ADMIN no cobra ni cierra turno ajeno mediante una excepción implícita. Se conserva el permiso actual de baja de ADMIN porque permite al responsable regularizar una pérdida comprobada; exige exactamente motivo, lote, autor, cantidad y controles del almacenero. La recepción/carga sigue reservada a ALMACENERO.

**C-01.** Dado vendedorA y venta/turno deB, cuandoA solicita ID directo o cambia filtros, entonces no accede al registro ni sus agregados; ADMIN sí consulta los globales. Costo de compra nunca aparece en constancia para cliente, incluso abierta por ADMIN.

**C-02.** Dado cada rol/visitante, cuando abre menú/página/URL directa, entonces disponibilidad y autorización coinciden; el encabezado ADMIN no ofrece «Nueva venta»/operar turno. Cuentas inactivas/revocadas no conservan acceso por cookie antigua.

**C-03.** Dado catálogo administrativo, cuando VENDEDOR lo solicita, entonces se deniega; en POS accede a nombre/código/precio/existencia vendible sin costo. La futura consulta sin turno es VEN04, no una ampliación tácita.

RN07/29, PROD01, CAJA05 y VEN02a/05a/b. No cambia datos existentes. Pruebas de roles, propiedades, cabeceras, navegación de regreso y errores deben cubrir navegador y solicitudes directas. Distinguir acceso vendedor a sus turnos cerrados de las ventas de otro turno/usuario.

## DOC-02-04 · Personal, reset y confirmación

**Decisiones.** Nombre completo120, no único; correo normalizado único máx254. Crear/editar mantiene RN24 actual; un reset administrativo explícito permite desbloquear y revoca sesiones, con evento de quién/cuándo/cuenta afectada, nunca la clave. Reactivación/cambio de correo por sí solos no reinician silenciosamente una sanción vigente; conservar el plazo/bloqueo asociado a la cuenta. Para un desbloqueo legítimo usar acción confirmada y auditada. Se evita depender del correo automático futuro.

**C-01.** Dada cuenta con turno abierto o último ADMIN activo, cuando se cambia rol/desactiva, entonces se respetan las invariantes existentes y el rechazo no cambia cuenta/sesiones/turno.

**C-02.** Dado un cambio de estado, cuando ADMIN confirma un resumen de nombre/correo/efecto, entonces se aplica el destino explícito; al cancelar o repetir el destino no se invierte accidentalmente. La advertencia explica acceso/sesiones y restricciones reales.

**C-03.** Dado reset explícito válido, cuando confirma ADMIN, entonces cumple RN24, revoca cookies antiguas, guarda evento sin secreto y solo entonces permite nuevo login. Cambio de correo/reactivación conserva bloqueo hasta expiración o desbloqueo explícito. Probar bloqueo viejo/nuevo identificador y carreras de ingreso/desactivación.

**C-04.** Dado un usuario sin turno/borrador, cuando sale, entonces el mensaje no afirma que tiene uno. Con turno abierto y borrador, confirma descarte, no cierre de caja; cancelar no cambia nada.

RN12/17/24/29/30, USR02..05, AUTH03. Conservar política uniforme de identificadores inexistentes/inactivos de AUTH01/02. Antes de canonicalizar IDNA, producir informe de equivalencias y colisiones entre Unicode/punycode; no fusionar cuentas. Datos y pruebas de identidad deben usar cuenta ID estable para bloqueo/revocación, sin reset accidental al renombrar correo. Longitudes254/255,120/121, Unicode/espacios y normalización se comprueban en todas las capas.

## DOC-01-06 · Seguridad técnica, tráfico y eventos

**Decisión de exposición.** Portal Django fuera de la navegación y acceso comercial; producción lo deshabilita o restringe a canal de mantenimiento autenticado y autorizado. No basta quitar enlace. Elegir configuración concreta al verificar despliegue; credenciales de mantenimiento no son cuentas compartidas de negocio.

**C-01.** Dado tráfico desde el punto de entrada comercial, cuando se solicita `/admin/` o `/admin/login/`, entonces no habilita otro camino de autenticación comercial ni elude límites. Probar perfiles staff/superuser ficticios y permisos por modelo en el canal autorizado.

**C-02.** Dado ingreso/salida/reset/cambio de rol/estado u operación crítica, cuando termina, entonces existe evento con fecha, actor cuando se conoce, acción, objeto, resultado y requestID sin secretos. Los eventos de mutación se guardan con la misma transacción de negocio; su emisión externa se hace tras commit o outbox, nunca como prueba de atomicidad por sí sola. El rechazo se deniega aunque falle el log; registrar diagnóstico sanitizado sin conceder acceso.

**C-03.** Dado error que contiene datos ficticios sensibles en `exc_info`/campos, cuando se registra, entonces no aparecen en destino/log. No confundir filtro con instrumentación.

**Investigación obligatoria.** SEC15TRAFICO: medir endpoint/punto de entrada/IP confiable y redes compartidas; proponer presupuesto/ventana y probar que limitar no bloquea toda la tienda tras NAT. SEC15RETENCION: separar contadores operativos de bitácora, finalidad/volumen/acceso y plazo; no borrar bloqueos activos ni contadores1–4 arbitrariamente. El contrato cuantitativo depende de información no disponible; sigue C, sin aprobación ficticia. Logging técnico actual no depende de pantalla HU-LOG-01 futura.

## DEC-10-BLOQUEO-INACTIVIDAD · Puesto desatendido

**Decisión.** Seleccionar HU-VEN-01a/RN22 como requisito antes del piloto; pantalla de ventas bloquea tras300 segundos de inactividad válida. Preserva borrador/turno, no cobra/descarta/cierra. Reautentica mismo vendedor; logout conserva su regla distinta. Es costo medio y más adecuado que suponer que bloqueo de ingreso15min protege una sesión abierta.

**C-01.** Dado puesto autenticado inactivo300s, cuando intenta consultar datos de venta protegidos o mutar, entonces servidor exige reautenticación, incluso desde otra pestaña/HTTP directo. Un overlay JavaScript solo no cumple.

**C-02.** Dada actividad válida del usuario, entonces reinicia reloj del puesto; polling, reloj de cliente modificado y reintentos automáticos no lo renuevan. Definir estado de bloqueo por sesión, compartido entre sus pestañas.

**C-03.** Dada contraseña errónea/usuario distinto/inactivo, entonces no desbloquea ni pierde borrador; protege intentos conforme RN17 sin mostrar secretos. Tras reautenticar revalida precio/stock/turno antes de operar. Pruebas reloj, pestañas, suspensión/reanudación y rechazo sin mutación; no equiparar con sesión única futura.

## DEC-05-LOTE-ESPACIOS · Identidades y límites de inventario

**Decisión.** Número comercial máx64, trim/mayúsculas/espacios consecutivos→uno, sin borrar guiones/separadores ni fusionar `AB 12` con `AB12`. Conservar presentación y original si necesario para trazabilidad. Antes de migrar, listar colisiones por producto/recepción; resolver con evidencia, no automáticamente.

**C-01.** Dadas variantes ` ab  12 ` y `AB 12`, cuando se comparan dentro de la misma recepción, entonces son el mismo identificador normalizado y la repetición se rechaza; `AB12` sigue distinta. Misma identidad comercial en otra recepción se rige por DOC03AI.

**C-02.** Dada carga/recepción, entonces cantidad entera1..999999, costo decimal0.0001..9999999.9999 (máx4 decimales), vencimiento>hoy Lima, código de lote1..64. Rechazar bool como entero, NUL, exponentes, signos ambiguos, precisión excedida y lote inexistente en operaciones que lo requieran.

Se ratifica el límite técnico de vencimiento hasta el aniversario de hoy+20 años; si el aniversario cae en día inexistente, usar el último día de ese mes, como `Lot.latest_expiration_date`. No es vida útil prescrita por ley. La UI actual ofrece cuatro tarjetas: omitir filas totalmente vacías si queda al menos una válida, validar simultáneamente las no vacías y rechazar `management_form` manipulado sin500. Cuatro tarjetas visibles no se convierte en máximo de negocio nuevo por inferencia. Límite defensivo de tamaño de solicitud/formset se verifica en seguridad antes de despliegue.

**C-03.** Dada cantidad mínima/ máxima y errores por campo, cuando se corrige el formulario, entonces preserva los valores válidos y muestra el error junto al campo/resumen accesible, sin consumir una clave exitosa. Probar medianoche UTC/Lima, producto/categoría/proveedor inactivados entre vista y POST.

## DEC-04-RUC-VALIDACION · Proveedor y estado explícito

**Decisión.** RUC:11 dígitos ASCII, único; esto valida formato, no existencia/estado SUNAT. Nombre1..160 normalizado para presentación (no único por homonimia), teléfono opcional hasta20 con el patrón vigente de formulario. El contrato no promete validación fiscal ni obliga integración externa. Costo bajo y apropiado para control interno.

Nombre debe contener al menos una letra o número; colapsar separadores blancos y rechazar NUL. Teléfono, cuando no está vacío, admite solo dígitos ASCII, espacios y signos `+ - ( )`, con al menos un dígito; colapsar espacios. Mostrar teléfono en lista (guion si falta). Búsqueda con NUL devuelve error controlado y cero filas, con opción de limpiar; foco en primer campo inválido y alerta accesible. Estos detalles implementados en muestras se ratifican desde este corte, sin atribuir aprobación comercial previa.

**C-01.** Dados proveedores homónimos, cuando se seleccionan/consultan recepción y registros, entonces nombre+RUC distinguen inequívocamente. El proveedor histórico inactivo permanece visible; solo los activos se eligen para nueva recepción, o se indica sin proveedor.

**C-02.** Dado POST de estado, cuando omite destino o envía otro valor, entonces rechaza; al repetir `activo=false`, permanece inactivo, no alterna. Actor ADMIN se revalida dentro de transacción; ALMACENERO consulta sin cambiar datos maestros.

**C-03.** Dado RUC inválido/duplicado o proveedor inactivado antes de confirmar entrada, entonces error claro y sin mutación; no convertir opción rechazada en omisión silenciosa. Describir «formato válido» sin insignia «validado SUNAT».

RN12 no gobierna proveedor; referenciar PROV01/02/04 y contrato de recepción. PROV03 edición sigue futuro. Revisar colisiones sin eliminar registros.

## RN-05 · Baja, ajuste y constancia

**Decisión.** Registrar causa real: vencimiento si se descarta por caducidad; daño solo antes de vencer; robo/faltante independiente de fecha, siempre con explicación y lote. No forzar vencimiento cuando se denuncia robo de unidades vencidas. Baja ADMIN o ALMACENERO; ajuste físico solo ADMIN; el estado comercial inactivo no impide corregir existencias reales. VENDEDOR nunca regulariza stock.

**Entradas.** Baja: lote, cantidad entera1..999999<=disponible, motivo de catálogo, explicación obligatoria daño/robo, clave. Ajuste: diferencia entera no cero en[-999999,999999], saldo no negativo; motivo1..300 sin NUL; lote existente o nuevo con fecha fiable/costo según DOC03AH. Existencia vencida encontrada puede registrarse por ajuste como **no vendible**, nunca recepción/carga inicial. Si no hay fecha fiable, se rechaza registro del lote y se investiga; no inventar fecha para permitir venta.

Para esta versión, el ajuste se habilita para productos con carga inicial confirmada. Evita que un ajuste previo sea sobrescrito por la fórmula de la primera carga. El arranque de un producto que solo tiene existencias vencidas y ninguna carga inicial necesita un procedimiento de apertura de inventario antes de admitirlo: se conserva como investigación de datos/operación, no se inventa una carga con unidades vendibles. Ese caso no puede pasar silenciosamente por recepción ordinaria.

**C-01.** Dado lote vencido con faltante comprobado, cuando ALMACENERO confirma robo con explicación, entonces baja por robo y conserva fecha/estado vencido; sin explicación rechaza. La baja no altera precio/caja/ventas y usa costo de salida de RN14.

**C-02.** Dado conteo ADMIN de lote nuevo, cuando aporta vencimiento fiable/motivo/costo requerido, entonces crea origen AJUSTE identificable, aumenta stock físico y solo cuenta como vendible si cumple estado y vencimiento. No consume una carga inicial ni simula compra.

**C-03.** Dada confirmación de baja, entonces hay constancia dedicada inmutable de referencia/fecha/autor/producto/lote/cantidad/motivo/explicación, consultable por ADMIN/ALMACENERO e imprimible si corresponde; no es ticket fiscal. HU-INV-02/CA-04 ya lo exige.

**C-04.** Dada concurrencia venta/baja/ajuste o doble POST, entonces no hay stock negativo ni duplicación; datos rechazados quedan intactos y reintento válido devuelve resultado anterior. Ajuste nuevo requiere pruebas de unicidad/colisiones.

Afecta INV02/03, RN03/04/05/14/20/29, DOC03AI. No añadir pantallas de cuarentena/recall/retiro proveedor de las propuestas RET a este alcance.

## DEC-08-KARDEX-COMPRAS · Movimientos, saldos y filtros

**Requisito.** HU-INV-04 es movimientos/Kardex; HU-INV-06 es historial de ajustes. Completar movimiento cronológico con saldo, referencia de recepción/carga/venta/baja/ajuste, responsable y lote; filtros de tipo/fecha definidos en HU. Referencia SOL solo cuando exista ese flujo, no inventada para entrada directa.

**C-01.** Dada secuencia de movimientos conocidos, cuando se consulta período/tipo, entonces muestra orden ascendente total por instante+ID y saldo inicial del período/saldo resultante correcto. Filtrar filas no recalcula el saldo real ignorando movimientos excluidos; explicar saldo de apertura/cierre y total filtrado.

**C-02.** Dada venta multilote, entonces su salida se puede atribuir a las asignaciones persistidas. Un lote legado no asignado se identifica como desconocido; no presentar asociación inferida como comprobada.

**C-03.** Dados ADMIN/ALMACENERO, entonces consulta no muta; VENDEDOR no obtiene costos. Aplicar paginación estable25 con filtros preservados y totales calculados sobre conjunto filtrado, no solo página.

Depende de RN25, DOC03AI/AH y diagnóstico de historia. Crear un saldo inicial de corte con procedencia si no se puede reconstruir pasado, después de autorización de datos; no inventarlo en esta fase. INV05/06 completas siguen futuras.

## DEC-07-VENCIDOS-FILTRO · Alertas y panel mínimo

**Decisión.** Separar «Próximos a vencer» (hoy<fecha<=hoy+días) de «Vencidos» (fecha<=hoy, stock físico>0), permitiendo consulta conjunta rotulada. Inventario vencido/inactivo sigue visible como problema físico. Alerta de reposición bajo mínimo aplica a producto y categoría activos con vendible<=mínimo. Panel mínimo muestra datos del día Lima, umbral30 días rotulado, vencidos y turnos según rol; no se afirma entregar DASH/REP completos.

**C-01.** Dado producto inactivo con unidades vencidas, entonces figura en vencidos con badge inactivo/no vendible; no dispara compra/reposición por stock bajo. Reactivar categoría no reactiva un producto suspendido.

**C-02.** Dado filtro días, entonces se valida entero ASCII en el rango de pantalla existente y se mantiene frontera temporal de Lima; al cambiar filtro, etiquetas/conteos/listado explican el mismo conjunto. No inventar1d/30d como obligación legal.

Rango ratificado del filtro actual:1..3650, predeterminado30; parámetro inválido informa y usa30 sin500. El número de días no cambia la frontera de lotes ya vencidos. OBS-00-15 ya tiene columna numérica `Existencias vigentes (UND)` en `catalog/templates/catalog/product_list.html`; no se pide crearla de nuevo. La prueba visual actual de todas sus combinaciones sigue en la matriz correspondiente.

**C-03.** Dado panel ADMIN, entonces totales diarios no se presentan como reporte por período, margen, gráfico, ranking o solicitudes implementadas. Medir volumen antes de aprobar índice parcial; un EXPLAIN pequeño no determina necesidad productiva.

## DEC-11-TOPE-EFECTIVO-FORM · Dinero y restricciones

**Decisión.** Venta nueva, efectivo entregado y apertura admiten hasta9,999,999.99 soles; precio/cantidades deben generar total dentro del límite antes de confirmar. Mantener precisión2 y redondeo vigente. Saldo esperado/contado/cierre acumulado admite capacidad `numeric(14,2)` (hasta999,999,999,999.99); no reutilizar el tope por operación para impedir cierre legítimo de suma de ventas. Diferencia puede ser negativa y debe equivaler a contado−esperado. Es un límite interno de interfaz/almacenamiento, no un umbral tributario.

**C-01.** Dados vacío/mínimo/máximo/máximo+0.01, exponente, signo extra, dígitos no ASCII y más de2decimales, entonces UI/servicio responden igual y no hay mutación en rechazo. Dinero siempre Decimal/centavos, nunca float.

**C-02.** Dado acumulado válido de varias ventas que supera el tope de una operación, cuando se cierra, entonces no se rechaza por ese tope; rechazar antes una venta que excedería capacidad acumulada y explicar capacidad, sin bloquear cierre de datos válidos ya registrados.

**C-03.** Dada inserción/actualización directa en base de prueba, entonces checks impiden cantidad de borrador fuera de1..999999, montos negativos donde no procedan y cierre incoherente. El check de cantidad>0 ya existe; PROP-10-04 exige añadir el máximo999999 faltante. Probar el signo negativo permitido de diferencia y límites del tipo.

Precio unitario nuevo no puede exceder el máximo de una venta. Diagnosticar precios legacy superiores antes de endurecer validación/constraints; no recortarlos ni reinterpretarlos automáticamente. El total y el efectivo revalidan su tope aunque cada precio individual sea válido.

PROP09DB01/PROP10-04, RN10/25/27, CAJA01/02 y VEN01c. Auditar datos antes de migración; no convertir NULL/inválido en cero sin evidencia.

## DEC-12-ORDEN-LINEAS-RECIBO · Consulta estable y UX

**Decisión.** Conservar orden de líneas del borrador en la venta nueva mediante posición persistida, independiente del UUID. Turnos ordenan apertura descendente con desempate por ID. Para legado sin posición, usar orden determinista declarado, sin afirmar que recupera la secuencia original. Paginación25 y filtros estables en listados crecientes; no añadir índices sin medición.

**C-01.** Dadas líneasA,B,C con UUID aleatorios, cuando se confirma y reabre constancia, entonces conservaA,B,C y snapshots; igualdad de instante en dos turnos siempre produce mismo orden.

**C-02.** Dado filtro válido/fecha incompleta/invertida, cuando consulta historial, entonces cumple el contrato de rango, muestra error claro sin500 para inválidos, preserva parámetros al paginar y abre detalle seleccionado. HU-VEN-05b/CA-02 es filtros y CA-03 es detalle; no exige expandir líneas en lista.

**C-03.** Dado rol ADMIN, entonces no ve topbar de vendedor ni enlaces operativos denegados; VENDEDOR puede volver a sus ventas/turno. En futuro no implementado, indicar estado sin botón que prometa acción disponible.

**C-04.** Dado GET de borrador, entonces no guarda precio nuevo automáticamente. Si precio/disponibilidad cambió, POST explícito/revisión previa al cobro informa y requiere aceptar contenido actualizado, conservando firma/identidad de borrador y validación final.

Afecta VEN01b/02a/05a/05b, CAJA05, PROP10-03, PROP12PAGINACION y menús. Pruebas empates forzados, varias páginas, dos pestañas, teclado,390×844 y impresión; repetir un test sin empate no demuestra arreglo.

## DOC-00-01 · Alcance y gobierno Scrum

**Decisión.** Adoptar R1 de consolidación: nueve HU originales más las adicionales auditadas de identidad/catálogo/proveedores/inventario/historia y bloqueo de pantalla previo al piloto. La lista exacta está en09. Conservar futuros y ocho ideas; no seleccionar SOL/Yape/reportes completos por estar escritos. Ratificar mínimos/nombres desde hoy, no fingir autorización anterior.

**C-01.** Dado cualquier HU del catálogo, entonces existe una única fila vigente en backlog, una fila por CA base en matriz y relación con encargos cuando cambian criterios. SP originales se identifican como estimaciones previas, no tamaño actualizado de trabajo restante.

**C-02.** Dados documentos01/02/03/07/08/09/14/16/20/21/CONTROL e informes00–12, entonces apuntan al mismo corte, separan historia y no mantienen dos estados actuales contradictorios.

**C-03.** Dado trabajo aceptado, entonces no se llama implementado hasta cambio autorizado, ni verificado hasta evidencia exacta. No asignar Sprint/fecha/persona/velocidad a partir de valores académicos viejos.

**C-04.** Dadas propuestas de límites/nombres de catálogo, entonces mínimo por defecto10, rango0..999999 y nombre producto único normalizado incluyendo inactivos preservan decisiones actuales; cualquier cambio requiere análisis de colisión y pruebas. Empleados/proveedores homónimos siguen permitidos: esa unicidad no se propaga a otras entidades.

## CT-ROLLBACK-01-POST-ESCRITURA · Verificación antes de piloto

**Investigación, no defecto probado.** Preparar entorno PostgreSQL17 aislado (objetivo de diseño), versión menor soportada y registrada; la evidencia18.4 existente sigue útil pero no demuestra17. No migrar ni actualizar el motor operativo en esta fase.

**C-01.** Dada escritura efectiva dentro de transacción aún no confirmada, cuando se termina el proceso servidor propio, entonces tras reconectar no quedan efectos parciales. Registrar barrera después de escritura que demuestre punto exacto de interrupción. Matar una espera anterior a escritura no cubre este caso.

**C-02.** Dado fallo/reinicio del motor aislado, entonces recuperación y reintento preservan unicidad/stock/caja. Distinguir resultado de caída antes/durante/después de commit; si respuesta se pierde tras commit, reintento recupera resultado existente.

**C-03.** Ejecutar E2E actual ADMIN→ALMACENERO→VENDEDOR→ADMIN, permisos cruzados, concurrencia por recursos compartidos, respaldo/restauración verificando integridad, CI real y despliegue seguro. Publicar comandos/versiones/datos/resultados/omisiones y revisión independiente.

**Límites.** Un análisis de código o test Client no acredita navegador, red HTTP real, PostgreSQL17, impresora física, telefonía, lector de pantalla o canal tributario real. Mantener C hasta prueba apropiada. Sin datos del negocio no se certifica normativa ni capacidad operativa. Las futuras etapas13–16 mantienen su inventario propio.

## Funcionalidades futuras y excepciones

Se conservan sin ejecución autorizada: AUTH04a/04b/05,USR06,LOG01 UI; CAT03/04,PROV03; INV05/06 y SOL01..05b; CAJA03/04/06/07 y VEN04 completo; VEN06a/b/c/07; CONF01/02; DASH01..05 y REP01..09; ocho ideas fuera de horizonte y PROP03RET multiproducto/cuarentena/recall. Aceptar la recomendación de diferirlas no equivale a aceptar todos sus criterios antiguos como listos para construir: correo/códigos, anulaciones, datos personales y fiscalidad necesitan refinamiento vigente cuando se seleccionen.

Las fichas propuestas anteriores siguen localizables por el índice de IDs. No se crean duplicados de HU para resolver pequeños complementos. Las etapas13–17 no se declaran terminadas por este registro.
