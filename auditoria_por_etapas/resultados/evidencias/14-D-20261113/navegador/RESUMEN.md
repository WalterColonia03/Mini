# Ejecución de navegador 14-D

Primera pasada, sublote 14-D, 13/11/2026 en Lima. El recorrido final es `recorrido3`, ejecutado entre 17:13:33 y 17:13:52. Conserva `recorrido1` y `recorrido2` como ejecuciones anteriores de esta sesión. Los 44 checkpoints finales corresponden a 41 observaciones de UI y 3 solicitudes POST directas con sesión del navegador. Se suman 14 capturas y 18 comparaciones del hash completo sin mutación. Estos conteos describen la muestra y no representan el total de criterios de las HU.

Chrome 157.0.8103.78, Playwright 1.65.1, Django 5.2.18 y SQLite 3.49.1. Se lanzaron tres contextos independientes, viewport 1280×900, idioma es-PE y zona America/Lima. El servidor WSGI local atendió HTTP real con middleware, CSRF, sesiones y autorización del producto. La fixture temporal únicamente creó roles, tres cuentas ficticias y CAJA-01. Categoría, producto, proveedor, lotes, borrador, venta, merma y cierre se crearon mediante formularios de la UI. Los secretos fueron aleatorios y no se conservaron. El servidor se detuvo, los contextos se cerraron y SQLite temporal se eliminó al terminar.

08 al comenzar tuvo SHA-256 `33d2f17067fec3bb30e018ef49b77d87f84adfd9bafe04adf19161cd286e47a4`. HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`. El manifiesto de 180 archivos de identity/catalog/inventory/cash/sales/config/templates/app_platform tuvo hash `849dba031ad52612261b94758562a8b277902dca586d4925f05ac6edb438472e`, idéntico al inicio y al final. Incluye las correcciones de descuentos y causas de merma de esta sesión. Su ámbito y algoritmo se describen en `build()` del runner, por lo que debe compararse por archivo con otros manifiestos. La revisión posterior confirmó cero archivos cambiados. [Manifiesto](recorrido3/build-final.json) · [Ejecución](recorrido3/ejecucion.json) · [Índice de evidencia](recorrido3/indice.json).

## Caso conectado y efectos

| Paso | Rol y dato | Resultado comprobado | Referencia funcional de 08 |
|---|---|---|---|
| 01–10 | ADMIN crea Familia 14D, Harina 14D / INT-14D-HARINA, precio 3,55, mínimo 5, Proveedor 14D / 20000000014 | Una fila de cada entidad, producto sin lotes; tipo interno seleccionado | HU-AUTH-01, HU-CAT-02, HU-PROD-02, HU-PROV-02 |
| 12–14 | ALMACENERO elige producto y proveedor, lotes PRIMERO 3 unidades con vencimiento 20/11/2026 (hoy+7) y SEGUNDO 7 con vencimiento 13/12/2026 (hoy+30), ambos costo 2,0000 | Total físico/vigente 10, promedio 2,0000, proveedor y autor de carga preservados en los dos lotes | HU-INV-01a, RN-03, RN-14 |
| 16–19 | VENDEDOR abre CAJA-01 con 100,00, busca código, agrega 4 | Borrador con 4, lotes siguen 3 y 7, cero ventas | HU-CAJA-01, HU-VEN-01b |
| 20–26 | Categoría inactiva y vuelta a activa por ADMIN; VENDEDOR conserva borrador y reintenta efectivo | Rechazos detallados abajo. Campo editable visible de cobro es Efectivo recibido, ausencia de input de descuento comprobada. JS devuelve 5,80 al ingresar 20,00 | PROP-E00-HU-02/J-CA2, HU-VEN-01c, DEC-11-DESCUENTOS-ALCANCE |
| 27–28 | VENDEDOR confirma 4×3,55 | V-00000001, total14,20, base12,03, IGV2,17, recibido20,00, vuelto5,80. FEFO3+1 descuenta lotes de [3,7] a [0,6]. Recargar conserva una venta | HU-VEN-01c, HU-VEN-02a, RN-19, RN-03, RN-25 |
| 29–32 | ALMACENERO consulta stock6, da baja de1 por daño con detalle | B-00000001, lote SEGUNDO baja6→5. Se conserva responsable y motivo. La interfaz retorna al selector con mensaje de éxito | HU-INV-02, RN-04, RN-05, RN-20, DEC-07-VENCIDOS-FILTRO |
| 33–36 | ADMIN consulta inventario, movimientos, ventas y constancia | Físico5/vigente5, entradas+3/+7, venta-4, merma-1, responsables, proveedor y referencias V/B. Historial y constancia coinciden en14,20/20,00/5,80 | HU-INV-04, DEC-07-VENCIDOS-FILTRO, HU-VEN-05b, HU-VEN-02a |
| 37–40 | VENDEDOR cierra contando114,20 | Esperado114,20, diferencia0, acta persistida y turno CLOSED. Recarga no duplica cierre. Preparar venta pide abrir turno | HU-CAJA-02 |

Los archivos JSON de cada paso conservan texto visible completo de body con menús, controles visibles con etiqueta/valor/tipo/límites/opciones y testigo de negocio. Los datos se consultaron con SQLite en modo solo lectura. La huella cubre todas las filas de todas las tablas catalog/inventory/sales/cash y el par rol/activo de las cuentas. Se excluyen sesiones, mensajes, último login y control de intentos, que cambian durante autenticación y rechazos. Las consultas posteriores confirman ventas, líneas históricas, stock, responsables, costo y cierre con valores explícitos. Los campos secretos, tokens CSRF, claves idempotentes y contraseñas se excluyen de los archivos.

## Rechazos, recuperación y límites

| Evidencia | Esperado y observado |
|---|---|
| 04, 11, 15 | GET en navegador ADMIN→abrir caja, ALMACENERO→historial ventas y VENDEDOR→stock devuelve403 visible. Todos conservan hash de negocio |
| 05b, 12b, 20b | POST directo autenticado ADMIN→carga, ALMACENERO→apertura y VENDEDOR→categoría devuelve403 con CSRF válido y huellas antes/después idénticas |
| 13 | Primer lote vence hoy en Lima; servidor dice «El vencimiento debe ser posterior a hoy en Lima.» No se guarda ninguno de los dos lotes ni carga/costo |
| 22–24 | ADMIN desactiva categoría con borrador revisado por VENDEDOR. Intento de cobro rechaza «ya no está disponible para la venta» sin mutación. Reactivación permite continuar |
| 25 | Efectivo14,19 frente a total14,20 produce error de insuficiencia sin venta, consumo de lote ni cambio de correlativo |
| 30b | Motivo VENCIMIENTO sobre lote vigente rechaza «El lote aún no ha vencido; seleccione la causa real de la baja.» Sin cambios de stock, costo, merma o correlativos |
| 31 | Merma7 frente a stock6 rechaza exceso, sin mutación. Luego merma1 por daño se confirma |
| 28, 33–36, 39–40 | Recargas y consultas del recorrido conservan los hashes completos esperados |

Se inspeccionaron visualmente las capturas finales 04,13,23,26,27,30b,34,38. Muestran rótulos, roles, mensajes y números legibles, sin superposición de controles en el viewport probado. La captura26 conserva el mensaje del rechazo previo hasta el siguiente envío, mientras el vuelto estimado reacciona al nuevo efectivo. Eso describe la validación de servidor tras un POST rechazado.

El ADMIN puede revisar los cuatro movimientos y el total actual5. La pantalla34 sigue sin mostrar asignaciones por lote para la venta y saldo después de cada movimiento exigidos por HU-INV-04/CA-01, filtros de CA-04 o la paginación especificada en CP-HU-INV-04-001. La venta persistida sólo tiene SaleLine y no un modelo de asignaciones por lote o movimiento de caja independiente, exigidos por DEC-11-MODELO-AUDITORIA-VENTAS y HU-VEN-01c/CA-04. Por tanto, el recorrido acredita consumo FEFO observado y cifras conectadas en esta muestra, y mantiene pendiente esa trazabilidad durable. La baja muestra B-00000001 en mensaje y en movimientos, con constancia propia aún pendiente de HU-INV-02/CA-04 y RN-05/C-03. Estos alcances parciales impiden convertir la ejecución exitosa en cierre de todas las HU.

No se ejecutaron en esta muestra expiración real al pasar medianoche, fallo post-escritura, bloqueo concurrente PostgreSQL, cierre con borrador concurrente, revocación de sesión, doble POST de cobro, impresión física, dispositivos móviles o lector de código. La fecha de frontera sí se probó al registrar lotes. Las pruebas de servidor y antecedentes relevantes deben enlazarse con sus propios límites y versiones.

## Reproducción y conservación

`recorrido.py` recibe un directorio nuevo y rechaza sobrescribirlo. Necesita el Python de r1-pmv, Playwright1.65.1 y Chrome estable instalado. En esta sesión Playwright se instaló en el directorio temporal `C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915` sin editar dependencias del producto.

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
r1-pmv/.venv/Scripts/python auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido.py auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/nueva-ejecucion
```

En otro entorno se puede instalar Playwright en un destino temporal propio y apuntar PYTHONPATH allí, o utilizar un entorno de prueba existente que ya lo incluya. `E14_CHROME` admite ruta explícita al ejecutable. Las fechas de lotes se calculan con el día actual de Lima, evitando caducidad del caso. El servidor usa un puerto libre y la base empieza vacía.

`recorrido1` completó40 checkpoints, anterior a la corrección del servicio de merma y con etiquetas de rol de fixture inicialmente iguales a los nombres de cuenta. `recorrido2` corrigió esas etiquetas y añadió tres POST directos sobre el build ya corregido. `recorrido3` añade la variante de motivo incompatible y es la evidencia final de44 checkpoints. Se conservan las tres ejecuciones sin sumar sus casos repetidos como cobertura adicional.
