# Ajustes documentados · etapa 14, primera pasada · 14/11/2026 Lima

La autorización vigente del usuario es corregir los pendientes necesarios hasta completar la etapa14. Esta implementación cumple contratos ya seleccionados, no crea un permiso desde el documento. La línea base anterior está en [14-CIERRE](../evidencias/14-CIERRE-20261114/build-antes.json) y su ZIP de producto; no se abrió ni migró la base operativa. Los cambios14-I y anteriores se conservan.

## Inventario previo y alcance aceptado

| Requisito | Necesidad y brecha previa | Realización |
|---|---|---|
| HU-INV-03/CA01 | ADMIN registra positivo en lote existente o nuevo, fecha fiable y costoRN14 | Servicio compartido para ambos modos; ruta existente y selector de producto para nuevo lote |
| HU-INV-03/CA02 | Negativo exige lote y no excede su saldo | Lote existente bloqueado; negativo en nuevo lote rechazado; saldos no negativos |
| HU-INV-03/CA03, INV04/CA03 | Fecha, cantidad, responsable y motivo conservados | PhysicalAdjustment ya tenía delta/fecha/motivo; agrega fotografías y detalle GET enlazado desde Kardex |
| RN05/C02 | Origen AJUSTE identificable, incluso lote vencido físico no vendible | Lot.adjustment_origin enlaza el registro que lo creó; no se fabrica recepción ni línea inicial |
| RN05/C04 | Reintento devuelve resultado anterior; divergencia/roles/errores no mutan | UUID única+huella persistentes y actor vigente en servicio; HTTP requiere UUID; no depende de sesión |
| RN14, DOC03AH/C03 | Q>0 usa promedio vigente; Q0 exige costo positivo y fuente | Campos opcionales en formulario, obligatorios según stock físico al confirmar; snapshot costo+fuente; no reescribe salidas previas |
| DOC03AI / DEC08 | Origen y cantidades originales no cambian con conteos | Se conserva InitialLoadLine/StockReceiptLine. initial_quantity sigue siendo capacidad técnica; se etiqueta origen de ajuste y no se cuenta como una entrada adicional en Kardex |
| RN29 / CT-COHERENCIA-UI | SoloADMIN modifica; ADMIN/ALM consultan detalle; errores recuperables | GET/POST autorizados en servidor; resumen enfocable y mensajes junto al campo, claves/datos retenidos |

Referencias de planificación: [08](../../../08_Historias_de_Usuario.md#HU-INV-03), [RN05](../../../08_Historias_de_Usuario.md#contrato-RN-05), [DOC03AH](../../../08_Historias_de_Usuario.md#contrato-DOC-03AH-01).02/16 requieren sincronizarse con esta concreción. INV05/06 globales y reportes futuros siguen fuera del alcance; no se añaden rutas de historial global. Producto sin carga inicial sigue rechazado conforme a08; no se inventa una apertura para existencias solo vencidas.

## Decisiones y alternativas

| Decisión / fundamento | Beneficio, riesgo, costo e impacto |
|---|---|
| Capturar en PhysicalAdjustment existente, campos nullable para legado | Reutiliza la operación que afecta stock, evita una tabla genérica duplicada. Costo medio por migración/lectura. NULL es historia no disponible, nunca se rellena con nombres actuales. Impacta ajustes, merma de nuevos lotes y Kardex |
| Lot.adjustment_origin OneToOne protegido como origen de un lote nuevo | Acredita procedencia; Kardex suma solamente el delta del ajuste. Alternativa bandera simple no prueba quién/cuándo/qué cantidad. Costo bajo/medio y dependencia circular resuelta dentro de transacción; FK inicial obligatoria se conserva solo como compatibilidad técnica |
| UUID única/huella por actor y contenido normalizado | Permite recuperar el mismo resultado entre sesiones y tras cambiar estado, costo o fecha. Alternativa50claves de sesión o ventana2s pierde deduplicación. Costo medio; exige que HTTP aporte su clave. Llamada interna sinUUID expresa operación nueva |
| Rechazar nuevo lote si número comercial normalizado ya existe | Un conteo no es otra recepción; se exige seleccionar la procedencia ya registrada. Evita duplicar origen o fusionar entregas ambiguas. No modifica la política de recepciónR1/R2; estas siguen pudiendo compartir lote comercial segúnDOC03AI. Costo bajo; claveproducto serializa colisiones |
| Q0 exige costo y fuente1..300; Q>0 conserva promedio y rechaza costo distinto | Permite regularizar conteo documentado sin inventar costos, conserva fuente visible. Costo bajo/medio. Referencia es declarada por operador, no autenticación legal del documento; datos desconocidos requieren investigación |
| Resumen de errores enfocable sin rediseño global | Guía ui-ux-pro-max: búsqueda`error summary validation` devolvió Focusable Error Summary y Error Messages; se retienen erroresinline, rolealert y foco solo al responder error. Costo bajo; accesibilidad integral no se deduce de este cambio |

La inmutabilidad es del historial a través de los flujos de aplicación. No se afirma resistencia a SQL privilegiado, revocación de permisos del administrador de base o archivo alterado manualmente. Esas garantías se controlan en seguridad/operación de etapa15.

## Contrato de interfaz y campos

| Ruta / actor / estado | Control o salida literal | Tipo, normalización, reglas y persistencia |
|---|---|---|
| /inventario/ajustes/nuevo/, ADMIN | «Ajuste por conteo físico», tabla Producto/Lote/Vencimiento/Disponible, «Ajustar» | Selecciona UUID de lote; no muta enGET; muestra referencia de recepción o «Origen AJUSTE {UUID}» |
| Misma ruta, selector nuevo | «Registrar un lote encontrado»; «Producto para lote nuevo»; «Registrar lote nuevo por ajuste» | Select name=producto, inicialmente vacío; solo productos con carga confirmada; GET?producto=UUID |
| ?lote=UUID / ?producto=UUID | lot_id o product_id oculto, idempotency_key oculto | UUID válido requeridoHTTP. Nueva clave enGET; errores conservan clave. Ambos objetivos enviados simultáneamente rechazan |
| Formulario existente/nuevo | «Ajuste (positivo=entrada, negativo=faltante)» | Inicial vacío; enteroASCII[-999999,999999], no0; nuevo lote requierepositivo; negativo<=saldo |
| Formulario | «Motivo del ajuste» | Requerido, strip,1..300 sinNUL; persistido original |
| Formulario | «Costo unitario documentado (S/)» | Inicial vacío, decimal positivo hasta9999999.9999, precisión4. Q0obligatorio; Q>0opcional y si enviado debe coincidirconpromedio; persistido costo efectivo |
| Formulario | «Fuente del costo» | Inicialvacío, strip y máximo300 sinNUL. Q0obligatoria; Q>0 sin fuente guarda «Promedio vigente sobre existencias físicas» |
| Solo nuevo | «Número del lote nuevo» | Inicialvacío, requerido,64, normaliza espacios y mayúsculas; noNUL; númeroexistente rechaza y pide seleccionar origen |
| Solo nuevo | «Vencimiento fiable del lote» | FechaISO requerida; hasta20años futuro; pasada/hoy admitida como no vendible; jamás inventada |
| POST | «Confirmar ajuste», «Cancelar»; «Revise los datos del ajuste» | Confirmación transaccional; cancelar vuelve selector; resumen rolealert enfocable con enlaces a campos inválidos |
| POST válido/replay | «Ajuste físico registrado correctamente.» / «Este ajuste físico ya fue registrado anteriormente.» | Redirige al mismo detalle de UUID; éxito emitido después de commit |
| /inventario/ajustes/{UUID}/, ADMIN/ALM | «Detalle del ajuste físico», «Ajuste confirmado», «Datos originales del conteo. Un ajuste no es una recepción de compra.» | GETsolo, nevercache; VEN403 y POST405. Sin edición de operación |
| Detalle | Referencia del ajuste, Fecha y hora de Lima, Responsable original, Producto original, Código original, Lote original, Vencimiento original, Origen registrado, Variación de unidades, Motivo, Costo unitario del ajuste, Fuente del costo | 12salidas originales; referenciaUUID, fechadd/mm/aaaaHH:mm:ss, delta con signo+unidad, costo4decimales, textoescapado. NULLmuestraNo disponible |
| Detalle legado | «Registro anterior o incompleto: la fotografía original de producto, lote, origen o responsable no está disponible. No se reconstruye con los maestros actuales.» | Muestra delta/fecha/motivo conocidos sin inferir nombres faltantes |
| Detalle / navegación | «Registro interno de ajuste físico. No es un comprobante de pago.»; «Registrar otro ajuste» soloADMIN, «Ver movimientos», «Ver inventario» | Leyenda nofiscal y rutas existentes. No se prometió impresión/constancia fiscal de ajustes |
| Kardex | «Ver ajuste»; «Fotografía histórica de ajuste no disponible. Consulte los datos conservados en su detalle.» | Snapshotautor/lote; los datos cuantitativos antiguos conservados permiten saldo si el resto del origen concilia |

Mensajes de servicio nuevos: costoQ0sinfuente, promedio nofiable, costo distinto alvigente, lote existente que no se debe duplicar, falta cargainicial, intento cambiar identidaddeloteexistente y nueva clave inválida. Son validaciones de los contratos citados, no decisiones comerciales nuevas. Los literales exactos están en servicios y snapshots de navegador del cierre.

## Archivos y evidencia

Modelo, forms, servicios, vistas, rutas, ledger, plantilla ajuste/detalle/origen y enlacesKardex; migración`0011_adjustment_history_and_origin`. Retira/reinstala la protecciónreceived_at durante reconstrucciónSQLite, igual que0008, conservando el trigger en ambos motores. Sin backfill. Nuevas pruebas`inventory/test_audit14j_adjustments.py`.

[Focal1](../evidencias/14-CIERRE-20261114/ajustes-focal-1/resultado.txt):28tests/3fallos de expectativas heredadas (UUIDahorarequerida, redirección a detalle, camposnullable de migración). Se conservan logs y se actualizan sin cambiar esperadosdelnegocio. [Focal2](../evidencias/14-CIERRE-20261114/ajustes-focal-2/resultado.txt):48/48en17.461s, fuentesestables y sin migración pendiente. Incluye10tests nuevos con subcasos.

Los10tests nuevos cubren secuencia10+2−3=9, historia trasrenombrado, reenvío entre sesiones, divergencia/revocación, lote nuevo con origenAJUSTE y una solaentradaKardex, costoQ0documentado yrechazos, nuevo vencido/inactivo físiconovendible, tipos/fecha/NUL/límites/roles, falta cargainicial, errores postwrite de registro/stock/costo en modos existente/nuevo y escapesHTML/legado. Testigos comparan todas las tablas denegocio. La suite heredada verifica migración de registros antiguos con camposNULL y conservación exacta de campos previos; los tests de migraciónLot ahora compruebanNULLdelorigen nuevo.

El agente PostgreSQL comunicó16/16 en[diagnóstico2](../evidencias/14-CIERRE-20261114/postgresql/diagnostico-2/results.json): incluye ajuste nuevo con mismaUUID concurrente, colisión comercial entreADMIN distintos, negativos que compiten y venta↔ajuste enambosórdenes. Esa evidencia conserva build propio; root ejecutará/sincronizará el corte final antes del cierre.

La regresión completa y navegador final son responsabilidad del cierre integrado: consultar manifiestos yETAPA14 vigentes; no se declaran aprobados por esta nota antes de terminar. Este archivo no modifica08,02,16ni estados deetapas y no declara completa la14 por sí mismo.

## Actualización del corte de verificación

La [primera regresión completa](../evidencias/14-CIERRE-20261114/ajustes-regresion-1/resultado.txt) ejecutó 630 pruebas: 629 pasaron y una falló porque el POST positivo de una prueba heredada omitía la UUID que ahora exige el contrato HTTP. El servidor rechazó correctamente la operación y no creó el ajuste. Se corrigió únicamente esa preparación de la prueba, añadiendo UUID; no se suavizó la regla ni se cambió el resultado de negocio esperado. La [revalidación focal final](../evidencias/14-CIERRE-20261114/ajustes-focal-final/resultado.txt) pasó 21/21 en 1.628 s, sin cambios de migración ni de fuentes durante la ejecución. La regresión integral definitiva se vuelve a ejecutar desde el cierre sobre el build congelado.

El complemento de Chrome [CI14-08/09](../evidencias/14-CIERRE-20261114/complementos-chrome-2/INFORME.md) pasó 15 observaciones en build estable `ec783ac6febb289f70efbda37d7e742ad1305088982ad1e4e6f6694549cdd172`: selectores vacíos, cuatro claves ausentes/inválidas sin mutación, nueva merma de origen desconocido, legado/cabecera incompleta/doble origen con saldo no disponible, recargas y denegación de vendedor. La fuente del runner y el primer corte se conservan. La preparación técnica de datos incompletos se distingue expresamente de las operaciones realizadas mediante navegador. No acredita diagnóstico ni saneamiento de una base operativa.

La implementación de inventario queda congelada para la revalidación integrada. No quedan cambios de producto propios pendientes en los contratos aquí seleccionados; el cierre de etapa requiere todavía que el responsable integre la evidencia final de todos los módulos y la documentación aceptada, sin elevar otras etapas a completadas.
