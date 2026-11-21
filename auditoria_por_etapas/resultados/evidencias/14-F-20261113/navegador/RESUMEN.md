# Navegador 14-F

Primera pasada, sublote14-F, continuación14-F-ASIGNACIONES-01. Se examinan las asignaciones FEFO durables, snapshots de vendedor/caja y orden persistido de líneas, con declaración de datos históricos desconocidos. Referencias DEC-11-MODELO-AUDITORIA-VENTAS/C-01,03,04, RN-19/25/26/28 y DEC-12-ORDEN-LINEAS-RECIBO/C-01. Sale representa el ingreso de efectivo por venta conforme a la equivalencia aceptada14-F. El Kardex completo conserva sus pendientes.

## Inventario previo de superficies

| Actor y pantalla | Acción/campo/salida | Referencia |
|---|---|---|
| ALMACENERO, inventario | Leer físico/vigente por producto, enlazar movimientos y carga | DEC-07-VENCIDOS-FILTRO; HU-INV-04 |
| VENDEDOR, apertura | Efectivo100, aperturaCAJA-01 | HU-CAJA-01 como dependencia |
| VENDEDOR, borrador | Buscar código, cantidad4Zeta y1Alfa, orden de adición y revisión | HU-VEN-01b; DEC-12-ORDEN-LINEAS-RECIBO |
| VENDEDOR, cobro/constancia | Efectivo20, total16,20, vuelto3,80; cabecera vendedor/caja; líneas producto/código/cantidad/precio/importe; leyenda interna; ausencia de costos | HU-VEN-01c, HU-VEN-02a, RN-19/25/26/28, DEC-11-MODELO-AUDITORIA-VENTAS |
| ADMIN, movimientos | Venta de4Zeta, lotesA/B, cantidad por lote, costo de salida, autor histórico; legado con datos no disponibles | HU-INV-04; DEC-11-MODELO-AUDITORIA-VENTAS/C-01,03,04 |
| ADMIN, historial y legado | Consultar V-00000000 con costoNULL y origen de lote desconocido; vendedor/caja/orden no disponibles | HU-VEN-05b, HU-VEN-02a; contratos históricos |
| VENDEDOR, cierre | Contado116,20, apertura100+venta16,20, diferencia0 | HU-CAJA-02 como dependencia |

Los JSON de cada paso registran rol/ruta/UTC, texto visible completo y campos con etiqueta/tipo/límites/opciones. Testigos SQLite de solo lectura incluyen todas las tablas de negocio, filas de ventas/líneas/asignaciones sin claves idempotentes y estructura de columnas. Las capturas permiten inspeccionar rótulos, números, mensajes y distribución. Login usa tres contextos separados con middleware y CSRF completos. Los cambios de maestros posteriores se realizan mediante un control técnico sobre la fixture local, declarados en control-maestros.json. Esa acción comprueba estabilidad histórica y no acredita interfaz de edición de maestros.

## Fixture

SQLite nueva contiene tres cuentas ficticias, cajaCAJA-01, dos productosUND y sus cargas/lotes creados por ORM. Zeta14F tiene códigoINT-14F-ZETA y precio3,55, conA3 vencimiento hoy+7 yB7 hoy+30. Alfa14F tiene códigoINT-14F-ALFA y precio2,00 conC2 hoy+40. Promedio1,0000 en ambos. Hay una venta legacyV-00000000 de1Zeta por3,55 en un turnoCLOSED, costoNULL y ausencia de asignaciones/snapshots/posición. Los saldos iniciales son fijados para la prueba y no se reconstruyen a partir de ese historial incompleto. La fixture se declara en fixture.json.

El vendedor agrega Zeta4 y despuésAlfa1, cobra16,20 con efectivo20 y vuelto3,80, y el stock cambia deA3/B7/C2 aA0/B6/C1. Luego se renombra el maestro del vendedor a «Venta renombrada14F», la caja aCAJA-RENOMBRADA-14F y Zeta a«Producto renombrado14F» con nuevo código. La constancia nueva debe seguir mostrando fotografía original y ordenZeta→Alfa. El legado debe indicar ausencia de datos históricos. El turno cierra116,20 exacto.

## BEFORE preservado

Corrida11 checkpoints/11capturas,13/11/2026 Lima20:39:20–20:39:30. Chrome157.0.8103.78, Playwright1.65.1, Django5.2.18 y SQLite3.49.1. Viewport1280×900, localees-PE, zonaAmerica/Lima. Plan08ddadb1091e8501a00c0ae9ff9da212bce65446000131f137cede389ebc5313ad. Build48d4094dc4767a0825ca2526549b6a15a573fafc0b8f07392fe506f4d58ab4b1 estable durante ejecución.

| Caso | Esperado | Observado anterior |
|---|---|---|
| Lotes asignados a ventaZeta4 |A3/B1 persistidos y consultables|Stock0/6 correcto, movimiento genérico-4, modelo sin asignaciones|
| Orden del recibo |Zeta luegoAlfa|Alfa luegoZeta, a pesar del orden del borrador|
| Cambio posterior vendedor/caja |Conservar Venta original14F/CAJA-01|Constancia cambió a datos maestros renombrados|
| Cambio de producto/código |Conservar producto/código original|Producto/código originales preservados|
| Legado sin snapshots/asignaciones/costo |Expresar dato histórico desconocido|Constancia muestra vendedor/caja actuales; movimientos muestra venta genérica sin advertencia|
| Importes, stock y cierre |16,20; recibido20; vuelto3,80; Zeta6/Alfa1; cierre116,20|Coinciden en esta muestra|

Se inspeccionaron visualmente04-constancia-original,07-constancia-reabierta,06-movimientos-original y10-constancia-legacy. comparacion-historia.json registra misma_historia=false y orden inverso en BEFORE. La ejecución completada indica que el arnés llegó al cierre, con esos incumplimientos observados. [Metadatos](antes/ejecucion.json) · [Comparación histórica](antes/comparacion-historia.json).

## Recorrido final de trazabilidad

La corrida final2 completó12 checkpoints y12capturas el13/11/2026 de20:52:44a20:52:52 Lima. Build184fuentes36de329a9d0eb30b1f91992a39dd82a575d3cc0d0dff94792162d819918187fe estable y compatible por archivo con el build final del producto. final/ conserva la corrida intermedia mientras aún cambiaban fuentes.

| Observación | Resultado |
|---|---|
| Lotes de venta |Zeta4 guardaA3/B1 y Alfa1 guardaC1. StockA0/B6/C1|
| Orden y encabezado |Zeta antes deAlfa. Vendedor original y CAJA-01 preservados después de cambiar maestros|
| MovimientosADMIN |Lotes/cantidad/vencimiento y costo1,0000 de la venta nueva. Legado con lotes/costo/responsable no disponibles|
| VENDEDOR intenta movimientos |403 y testigo de negocio idéntico|
| Constancia antigua |Vendedor y caja no disponibles, orden original desconocido, importes previos intactos|
| Cierre |Venta16,20, apertura100, contado/esperado116,20, diferencia0|

Se inspeccionaron visualmente final2/06-movimientos-original,07-constancia-reabierta y10-constancia-legacy. La tabla permite leer cantidades por lote y la ausencia del legado. La constancia nueva mantieneZeta→Alfa y los nombres originales dentro del documento, mientras la navegación identifica al empleado actual. Las capturas incluyen el aviso interno literal y no muestran costo en constancia. [Ejecución](final2/ejecucion.json) · [Comparación](final2/comparacion-historia.json) · [Movimientos confrontados](final2/movimientos-confrontados.json).

## Revalidación de la cadena completa

Se reutilizó el runner conservado14-D sobre una base nueva y build14-F, en cadena-final/, de20:52:56a20:53:16 Lima. Completó44 checkpoints y14capturas, con184fuentes idénticas al recorrido específico. Los nombres de datos14D identifican la fixture reutilizada. La ejecución y versión corresponden a14-F.

ADMIN creó categoría/producto/proveedor mediante formularios. ALMACENERO registró lotes3+7 con costo2. VENDEDOR abrió caja100 y preparó venta4×3,55. Se desactivó y reactivó categoría, se rechazó efectivo insuficiente y luego se cobró14,20 con efectivo20/vuelto5,80. El stock quedó6, la merma1 dejó5 y ADMIN observó asignaciones3/1 en movimientos. VENDEDOR cerró114,20 exacto.

La cadena revalidó roles denegados mediante navegación y tres POST directos, carga con vencimiento inválido, cobro de producto inhabilitado, merma por causa incompatible/cantidad excesiva y venta sin turno. Los testigos conservan los rechazos sin mutación. Se inspeccionaron34-movimientos y38-cierre. [Ejecución](cadena-final/ejecucion.json) · [Movimiento](cadena-final/34-movimientos.json) · [Cierre](cadena-final/38-cierre.json). El recorrido flujo-completo/ anterior completó44 pasos mientras cambiaban pruebas y fue sustituido por cadena-final/ como corte estable.

## Reproducción

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
r1-pmv/.venv/Scripts/python auditoria_por_etapas/resultados/evidencias/14-F-20261113/navegador/recorrido_asignaciones.py auditoria_por_etapas/resultados/evidencias/14-F-20261113/navegador/repeticion-nueva --final
```

Para otra ejecución se requiere directorio de salida nuevo, Python de r1-pmv, Playwright y Chrome estable. PYTHONPATH apunta a la instalación temporal de esta sesión y debe adaptarse si se reproduce en otro equipo. El runner reutiliza soporte14-D en su ruta conservada. El puerto es libre de loopback, las contraseñas efímeras y la base temporal se elimina al cerrar. E14_CHROME permite elegir ejecutable explícito.

Para repetir la cadena completa, ejecutar el runner14-D/recorrido.py con un directorio nuevo dentro de14-F. Impresión física, dispositivos, concurrencia y totalidad de cada formulario conservan su cobertura propia. La variante parcial de asignación y FKproductoNULL se probó por servidor, sin recorridoChrome específico.
