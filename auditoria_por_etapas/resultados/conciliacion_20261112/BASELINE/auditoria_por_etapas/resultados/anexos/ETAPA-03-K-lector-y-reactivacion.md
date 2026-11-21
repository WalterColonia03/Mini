# Etapa 03-K · Lectura física de códigos y reactivación

10/11/2026, America/Lima. Este corte comprende HU-PROD-03/CA01 en el alta de ADMIN y la aclaración de HU-PROD-05/CA02. El inventario previo identifica las superficies, las fuentes y los archivos protegidos. El catálogo conserva 9 HU, 27 CA base y cuatro criterios suplementarios de estado de categoría. [Inventario previo](../evidencias/03-K-inventario-20261110T173128542047Z.json) · [Matriz individual](ETAPA-03-inventario.md).

## Lectura física · HU-PROD-03/CA01

**PARCIAL en la prueba física.** La cámara adquirió ambas etiquetas. La ficha de alta quedó vacía en ambas pruebas. El enlace entre teléfono, servidor de escritorio y campo de Django sigue sin acreditarse. HU-PROD-03 conserva la clasificación PREVISTO/FUTURO de 09. El aviso inmediato de duplicado, CA02, sigue pendiente de incorporación. El mensaje «Este campo es obligatorio» observado al enviar vacío corresponde a la validación del formulario.

| Intento | Evidencia en el teléfono | Evidencia en Chrome y servidor Django |
|---|---|---|
| EAN-13 impreso `0012345678905` | El operador informó que leyó y envió la etiqueta. El historial móvil muestra dos filas `012345678905` con exclamación roja. | Cero eventos de entrada en Código. Un POST devolvió la ficha con el error de campo obligatorio. Cero productos. El soporte del primer intento no identifica el origen de ese POST. [Observación](../evidencias/03-K-physical-20261110T173526027077Z/physical.json) · [Pantalla](../evidencias/03-K-physical-20261110T173526027077Z/02-resultado.png) |
| EAN-13 impreso `0012345678912` | Dos filas `012345678912` con exclamación roja. El operador confirmó el intento en la ventana de prueba. | El foco se registró en Código y luego en el botón de confirmación de la prueba. Cero eventos de entrada, Enter, Tab y POST. Cero productos. [Registro](../evidencias/03-K-physical-20261110T174028204311Z/physical.json) · [Captura del teléfono](../evidencias/03-K-physical-20261110T174028204311Z/03-telefono.png) |

La app móvil 5.0.9 (wire 4.9.100) mostró «Conectando…» y que no podía acceder al servidor. Barcode to PC Server 3.18.1 estaba abierto y mostraba cero dispositivos conectados al comprobarlo. La dirección seleccionada en el móvil no coincidía con una IPv4 activa del PC. Una lectura local de las conexiones TCP de Windows tampoco encontró ningún proceso escuchando en 57891, puerto publicado por el fabricante. Estas observaciones son posteriores a los intentos. El perfil de salida y la compatibilidad entre esas versiones quedan sin verificar. El aviso móvil de sonido trata del volumen. Se conserva la transcripción de la pantalla de conexión sin el nombre del equipo, su dirección ni el QR. [Observaciones del operador y el PC](../evidencias/03-K-physical-20261110T174028204311Z/operator.json) · [Conexión según el fabricante](https://barcodetopc.com/frequently-asked-questions/).

En las dos etiquetas EAN-13 con cero inicial, las barras admiten la representación UPC-A de 12 dígitos que mostró el teléfono. Esto importa para el catálogo, que admite identificadores de texto y distingue esas dos cadenas. No se cambió la normalización. La siguiente prueba utilizará Code 128 con el texto literal `00CAT03K`, que permite comprobar los ceros y el transporte de forma independiente de la interpretación EAN/UPC. Si el negocio usa ambas representaciones GTIN, queda por acordar qué valor almacenar y cómo tratar los códigos existentes. [Especificaciones GS1, §5.2.2.3](https://documents.gs1us.org/adobe/assets/deliver/urn%3Aaaid%3Aaem%3Aafbf55ad-0151-4a0c-8454-d494c0dc9527/GS1-General-Specifications.pdf) · [Etiqueta de control](../soporte/audit03k_code128.svg).

## Reactivación · HU-PROD-05/CA02

**CUMPLE en la muestra.** El usuario aceptó PROP-03E-CA01. Se actualizó el criterio existente en 08 y sus referencias en 03 y 21. Se prepararon cinco fichas inicialmente inactivas. ADMIN las habilitó mediante el catálogo. En cada caso el servidor respondió al POST con 302 y el catálogo mostró la activación. ALMACENERO consultó desde «Catálogo de productos» y VENDEDOR, con turno propio abierto, buscó cada código antes y después desde «Preparar venta». Las cinco búsquedas previas excluyeron el producto.

| Ficha reactivada | Lo que vio ALMACENERO | Oferta al VENDEDOR |
|---|---|---|
| Categoría activa, 19 unidades futuras, 5 que vencen hoy y 8 ya vencidas | 19, Disponible | 19 a S/ 8,50 |
| Categoría activa, sin lotes | 0, Sin stock vigente | Ausente |
| Categoría activa, 3 unidades que vencen hoy en Lima | 0, Sin stock vigente | Ausente |
| Categoría activa, 4 unidades vencidas ayer | 0, Sin stock vigente | Ausente |
| Categoría suspendida, 7 unidades con vencimiento mañana | 7, Categoría desactivada | Ausente |

**31/31 comprobaciones de Chrome, respuestas HTTP y persistencia**. La constancia conservó su texto. Las cinco fichas terminaron activas y conservaron los demás campos observados. Se cotejaron también seis lotes, cargas, categorías, una venta y su línea, dos borradores con sus líneas y el turno abierto. **8/8 métodos Django** de disponibilidad pasaron con las comprobaciones de configuración y migraciones. El primer recorrido de navegador buscó el enlace de ADMIN en la sesión de ALMACENERO y terminó antes de ejecutar los casos. Se corrigió el soporte y se repitió en otra base. Un arranque previo de la prueba física también se detuvo antes del login por la longitud del desafío de aislamiento. [Prueba final](../evidencias/03-K-browser-20261110T173927046544Z/browser.json) · [Datos iniciales](../evidencias/03-K-browser-20261110T173927046544Z/fixture.json) · [Datos finales](../evidencias/03-K-browser-20261110T173927046544Z/orm-final.json) · [Pruebas Django](../evidencias/03-K-tests-20261110T174235672078Z/tests.txt) · [Intento de navegador anterior](../evidencias/03-K-browser-20261110T173808145023Z/browser.json) · [Arranque físico anterior](../evidencias/03-K-physical-20261110T173453359047Z/result.json).

## Reproducción y cursor

Desde la raíz del proyecto, en PowerShell, ejecutar los casos secuencialmente. Cada invocación crea su propio directorio marcado. El formulario se sirve en loopback. Chrome 157.0.8103.39, SQLite aislada, cuentas ficticias y pruebas Django en memoria. La etiqueta y el botón de confirmación son instrumentos del ensayo inyectados en el navegador. El soporte enfoca el campo de código y observa el resultado. La entrada física depende del operador.

```powershell
$runner = 'auditoria_por_etapas/resultados/soporte/audit03k_run.py'
$python = 'r1-pmv/.venv/Scripts/python.exe'
& $python -X utf8 $runner tests catalog.test_audit03_availability
& $python -X utf8 $runner browser
$env:AUDIT03_SPECIMEN = '00CAT03K'
& $python -X utf8 $runner physical
```

**Cursor 03-K2 / HU-PROD-03 CA01 / PROP-03G-SCAN-T01.** Comprobar primero que el servidor local escucha y que el teléfono y el PC están en la misma red. En la pantalla «Servidor» del teléfono, usar «Escanear código QR» con el QR actual del PC. Verificar «Conectado» y al menos un dispositivo en el servidor antes de abrir una nueva ficha. Escanear `00CAT03K` una sola vez en una sesión móvil nueva, comprobar ese mismo texto en móvil, servidor y campo, y cotejar eventos, POST y filas creadas. Registrar versión y perfil. Si el servidor sigue sin escuchar, comprobar sus avisos de inicio y la combinación de versiones compatible con el sistema y la licencia. [Guía oficial de vinculación](https://barcodetopc.com/settings/common-issues/) · [Rama 3 y versiones publicadas](https://barcodetopc.com/updates/v4/).

Las bases protegidas y el XLSX conservaron su contenido. Los servidores Django de prueba terminaron y el programa Barcode to PC quedó abierto para el operador. Sin cambio funcional en Django ni migración sobre la base de uso. PostgreSQL, la suite global, el aviso inmediato de duplicado con lector y las carreras con cobro/entrada quedaron sin ejecutar en 03-K. Las demás etapas conservan su estado.


## Continuación 03-K2

El 10/11/2026 a las 12:58 Lima, después de que el usuario informó la conexión, la lectura física Code 128 llegó al campo ADMIN como 00CAT03K, con ocho eventos de entrada y ambos ceros iniciales. Se observó inmediatamente Enter, envío POST y navegación a la ficha registrada. La base aislada guardó exactamente un producto con ese código, precio 8.50, mínimo 10, UND y vencimiento obligatorio. HU-PROD-03/CA01 CUMPLE en esta muestra física. La propuesta de revisar antes de guardar queda pendiente de ajustar el perfil de salida. El perfil interno del lector y sus versiones después de la reconexión no se inspeccionaron. La prueba acredita el resultado de extremo a extremo en navegador y persistencia, con conexión informada por el operador. El servidor Django finalizó y todos los archivos protegidos conservaron sus hashes.

**Cursor 03-K3 / PROP-03G-SCAN-T01.** Configurar la salida del lector para enviar el código sin Enter y repetir una lectura física en alta nueva, verificando campo exacto, cero POST y cero productos hasta pulsar Registrar. Después abordar el aviso inmediato de duplicado de HU-PROD-03/CA02, que sigue previsto.
