# Dinero y cierre de caja · primera pasada14 · 14/11/2026 Lima

La revisión de08 DEC-11-TOPE-EFECTIVO-FORM/C01..03 detectó que el formulario y servicio de cierre reutilizaban el máximo por operación: dos ventas válidas podían impedir cerrar. También se admitía total nuevo superior al límite, faltaban checks seleccionados y el precio normalizaba signos/dígitos ambiguos antes de validarlos. El usuario autorizó corregir los pendientes necesarios para completar14; se implementa el contrato ya aceptado, sin cambiar el umbral comercial ni habilitar descuentos nuevos.

| Fuente / pantalla, rol y acción | Campo/salida y contrato | Implementación y evidencia |
|---|---|---|
| HU-CAJA-01, DEC11C01; `/caja/abrir/`, VENDEDOR; «Abrir turno» | Monto inicial; requerido Decimal2,0..9999999.99, inicial0; no signos extra/exponente/Unicode | cash/forms/services; M01..03, pruebas cash.test_audit14closure_money; otros roles no abren en cadena |
| HU-PROD-02/04; alta/edición ADMIN; guardar | Precio de venta requerido, positivo hasta9999999.99, escala2; servidor exige Decimal finito sin exponente positivo; no float/string ambiguo | catalog/forms/services; catalog.test_audit14closure_price. El máximo no se aplica retroactivamente a recuperación idempotente conocida |
| HU-VEN-01c, DEC11C01; `/ventas/cobrar/`, VENDEDOR; «Confirmar cobro» | Efectivo recibido requerido; dos decimales, mínimo total, máximo9999999.99; total nuevo positivo≤máximo; no descuento discrecional nuevo | sales/forms/services; M04..08 y tests. Total y vuelto en constancia, cantidad y costo en persistencia; rechazo no consume contador/stock/clave |
| DEC11C02; cobro bajo bloqueo del turno | apertura+suma de totales confirmados+nueva venta≤999999999999.99 | Se comprueba antes de escribir. Mensaje «La venta excedería la capacidad acumulada del turno. Cierre el turno antes de registrar otra venta.»; SQLite y PG `money_capacity` |
| HU-CAJA-02, DEC11C02; `/caja/cerrar/`, VENDEDOR; «Cerrar turno» | Efectivo contado requerido, Decimal2,0..999999999999.99; esperado=apertura+totalventas, diferencia=contado−esperado puede ser negativa | M10..13:1e12 rechazado sin mutar,10000000 aceptado y recargado; prueba capacidad máxima y diferencia0.01/−5. Cierre usa totales, no efectivo entregado |
| RN25/28; reenvío de cobro histórico | UUID/actor/borrador/montos originales coincidentes recuperan la misma constancia, efectivo y descuento históricos hasta14,2 | ConfirmedCheckoutRetryForm y sales.test_audit14closure_retry; HTTP no crea venta/caja/stock nuevo. Divergencia conserva rechazo |
| DEC11C03; persistencia | Cantidad borrador1..999999; Sale dinero no negativo≤14,2; cierre contado/esperado/diferencia acotados y ecuación coherente | sales0007/cash0004, checks PostgreSQL y SQLite. Diagnóstico previo impide endurecer datos incompatibles sin cambiarlos |
| DEC12C04; ADMIN edita precio10→12 con borrador abierto | GET no cambia precio. POST informa nuevo precio y exige confirmación revisada; aún no cobra | P01..08: único cambio de esa revisión permitida es sales_saledraftline; stock/caja/ventas/contador iguales. Segundo POST revisado confirma12, cierre112 |

Las claves/firma/subtotal ocultos pertenecen al protocolo de confirmación, no son campos de negocio editables. Las pantallas y leyendas monetarias previas se inventariaron en [14-D](14-D-inventario.md) y las constancias en [14-F](14-F-inventario.md). Los JSON de Chrome conservan texto visible, controles, rol, ruta y huella de cada tabla; los tests sirven para fronteras que el navegador normaliza antes de enviar. No se usa float para dinero del producto; los números JSON de testigos son una representación de inspección de SQLite, no cálculo de negocio.

## Decisiones y recomendaciones

| Necesidad / clasificación | Decisión, beneficio, riesgo, costo e impacto |
|---|---|
| Separar tope de venta y acumulado: corrección aceptada, implementada y revalidada | Evita caja imposible de cerrar y overflow. Costo bajo/medio, afecta catálogo/ventas/caja. Mantener un tope único contradice08. No supone que el negocio maneje esos importes reales |
| Checks y diagnóstico antes de migrar: tarea técnica/NFR de integridad aceptada | Segunda defensa contra escrituras fuera de servicios; costo medio, riesgo de bloquear migración si hay datos incompatibles. Se detiene con conteo y diagnóstico, nunca redondea/recorta historial. Operación real exige etapa15 y autorización propia |
| Preservar reenvíos históricos: corrección de RN25/28 aceptada | Evita que un cambio de política o formulario impida recuperar una venta confirmada. Riesgo de permitir nuevo descuento se evita mediante identidad y montos exactos de venta existente. Costo bajo |
| Validación antes de conversión: corrección C01 aceptada | Misma interpretación entre UI/servicios; evita signos/dígitos inesperados. Costo bajo; integra pruebas positivas y negativas de alta/edición, no una nueva HU |
| Precio cambiado requiere revisión: revalidación de diseño existente | El POST explícito actualiza solo el borrador y explica el nuevo precio; segunda confirmación cobra. No es un error con mutación parcial ni actualización silenciosa porGET. La primera expectativa del runner fue corregida contra DEC12C04, sin cambiar producto |
| Orden empatado del historial de turnos: deuda adyacente12/15 | Conserva la observación independiente sobre desempate; no se seleccionó como salida ordenada de14 ni se declara aprobado DEC12C01 completo. Beneficio: lectura estable; costo bajo, impacto consulta, sin alterar cadena monetaria. No aceptación nueva por este informe |

No se modificaron moneda, régimen fiscal, IGV, autorización externa de compras ni datos reales. No se añaden historias comerciales: las omisiones corresponden a criterios y tareas ya aceptados. Las decisiones externas desconocidas conservan alternativas/investigación de15/16.

## Ejecución reproducible

Desde la raíz, usar el Python de `r1-pmv/.venv` y `evidencias/14-CIERRE-20261114/servidor.py SALIDA_NUEVA cash.test_audit14closure_money catalog.test_audit14closure_price sales.test_audit14closure_retry`. Ese runner establece SQLite en memoria antes de iniciar Django y no usa la base operativa. Para Chrome, ver los scripts `recorrido_dinero.py` y `recorrido_precio.py` del mismo corte; generan una SQLite temporal y un servidor WSGI en loopback, con cuentas aleatorias ficticias y evidencia sanitizada.

[Regresión final](../evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt) · [Dinero Chrome](../evidencias/14-CIERRE-20261114/navegador/dinero-final/ejecucion.json) · [Precio Chrome](../evidencias/14-CIERRE-20261114/navegador/precio-final-2/ejecucion.json) · [PG](../evidencias/14-CIERRE-20261114/postgresql/INFORME.md) · [Revisión independiente](14-CIERRE-revision-independiente.md).
