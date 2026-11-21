# 13-B · Navegador, primera pasada · 13/11/2026 Lima

> **Corte histórico.** El bloqueo descrito aquí se resolvió el 13/11/2026. El recorrido posterior incluye los tres roles y el cobro confirmado por interfaz. [Evidencia final](13-B-final-navegador.md).

Estado: **PARCIAL por bloqueo externo del control de navegador**. Este anexo conserva lo realmente observado; no sustituye el navegador por Django Client.

## Entorno y evidencia

Se verificaron HEAD y los178 hashes de producto contra13-A antes de reutilizar su evidencia: la comprobación inicial del agente documental informó sin diferencias. La captura posterior [baseline13-B](../evidencias/13-B-20261113/baseline.json) ya recoge dos plantillas modificadas por el sublote paralelo (dashboard y stock_overview): **es un manifiesto intermedio, no una prueba íntegra de la entrada sin cambios**. La versión08 inicial es `5735fb283b70bca02ed551e0000c72df2025eaef9b977607b1e4a2b890e5a1d9`. Las observaciones siguientes corresponden a las superficies heredadas corregidas de13-A, con un servidor iniciado antes de las correccionesPython13-B; **no acreditan el build final13-B**. Fixture nueva SQLite `etapa13-20261113T163702Z-6b5d1381`, día Lima obtenido dinámicamente13/11/2026, servidor127.0.0.1:8134, navegador real integrado CUA, cuenta ficticiaADMIN. Claves en TEMP, nunca en evidencias.

| Caso | Ejecución / resultado observado | Evidencia y limitación |
|---|---|---|
| B01 | Login muestra «Productos, empleados, proveedores y resumen diario de ventas.»; no promete reportes. IngresoADMIN por formulario correcto. | [Captura](../evidencias/13-B-20261113/B01-login.jpg). El txt es un diff de accesibilidad, no DOM completo. |
| PanelADMIN | Siete cifras3 / S/60,06 / S/5,06 /1 /3 /6 /5. Fecha13/11/2026 · Lima; distingue ventas/descuentos del día de turnos/existencias actuales; pide actualizar la página. | Árbol completo observado en salida de herramienta en la sesión. Sin captura persistida propia; no usar para afirmar cobertura visual final. |
| B02 | Catálogo: categoría inactiva conserva4 unidades y mínimo99 sin badgeStock bajo; producto inactivo conserva8 y mínimo99 sin badge. Igual mínimo5/5 sí muestraStock bajo. | [Captura](../evidencias/13-B-20261113/B02-catalogo.jpg), árbol completo en salida de herramienta; txt es diff. No se cambió estado ni stock. |
| B03 | MenúVencimientos abre11 lotes:5vencidos y6próximos en30días. Vencimiento hoy aparece bloqueado; inactivos físicos permanecen. | [Captura](../evidencias/13-B-20261113/B03-vencimientos30.jpg), txt es diff. |
| B04 | Campo días30→1 y botónFiltrar:7lotes=5vencidos+2próximos. Fecha corte14/11. | [Diff](../evidencias/13-B-20261113/B04-vencimientos1.txt); contenido de tabla observado en herramienta. |
| B05 en adelante | Intento de rellenar3650 falló antes de ejecutar; sin cobro ni navegación por otros roles en13-B. | NO EJECUTADO. No trasladar las capturas13-A a estas correcciones. |

Las capturas se conservaron en JPEG sin credenciales. Los tres primeros txt guardan diffs, una limitación del arnés detectada al revisar archivos: futuras capturas deben pedir `disableDiffing:true` o DOM completo. No se reconstruyeron archivos como si fueran DOM capturado.

## Recuperación intentada y límite

1. Al iniciar el servidor, la primera navegación devolvióERR_CONNECTION_REFUSED porque el proceso aún no estaba iniciado. Se arrancó el servidor y se abrió nueva pestaña válida; recuperación exitosa, sin cambiar permisos.
2. Después de la interrupción de la sesión y «continua», la acción sobre el filtro devolvió `Local browser access is unavailable for this chat`.
3. Se intentó listar pestañas en el navegador seleccionado: mismo error.
4. Se reinició cua_repl y consultó inventario: aplicaciones nativas disponibles, lista de navegadores vacía y mismo error.
5. Se intentó la alternativa nativa documentada CUA sobre la ventanaBrave identificada por inventario. La herramienta detuvo Computer Use porque no pudo determinar con suficiente confianza la URL para aplicar su política. Se respetó la detención; no se intentaron controladores alternativos para eludirla.

**Acción que desbloquea:** restaurar el acceso de navegador autorizado para este chat, o continuar en una sesión con ese acceso operativo. No hace falta cambiar políticas de la aplicación ni datos operativos. Luego reiniciar el servidor del build identificado y usar fixtures nuevas para integrar el cobro.

## Estado de datos y cursor exacto

[Testigo de BD, conexiónSQLite mode=ro](../evidencias/13-B-20261113/browser-db-before-checkout.json): cinco ventas semilla (tres del día), ningún borrador creado en13-B y lote de integración3. La fixture13-A histórica sigue intacta con su borrador, sin atribuirle un cobro. El testigo de BD no equivale a un recorrido de interfaz.

Cursor **13-B-01 visual final**: entrar en fixture nueva contra08/build final y capturar panel de los3roles, catálogo/login, filtros1/3650/0/3651/inválido→30, enlaces y significado, incluyendo textos modificados13-B. Continuar **13-B-02** en fixture nueva independiente:2×3.55, demostrar borrador sin efecto, cobrar7.10 con10recibidos y2.90vuelto, recargar sin duplicado y comprobarADMIN4/67.16/5.06/1/4/6/5, almacén4/6/5, lote3→1. Continuar **13-B-03 visual**: vacío real, error/reintento, denegaciones/roles inválidos, D11, foco/teclado/pantalla estrecha. Las pruebas servidor/PG se registran aparte y no cubren estas omisiones.

No se declara finalizada13. Al cerrarla con evidencia suficiente, sigue14; no se inició14 ni la segunda pasada.
