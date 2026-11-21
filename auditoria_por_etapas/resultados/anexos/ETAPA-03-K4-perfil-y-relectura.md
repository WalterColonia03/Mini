# Etapa 03-K4 · Perfil del lector y repetición

## Continuación 03-K4 · perfil y lecturas repetidas

10/11/2026, America/Lima. Se comprobó por la interfaz de Barcode to PC Server un dispositivo conectado y el registro 00CAT03K. La plantilla Output template 1 tenía BARCODE y ENTER. Al alcanzar el límite de plantillas de la licencia, se ajustó la existente a solo BARCODE y se guardó. La primera repetición posterior conservó Enter y produjo una ficha aislada. El servidor seguía mostrando solo BARCODE. Después, el usuario confirmó haber reabierto la app móvil y creado una sesión nueva.

Las dos repeticiones siguientes registraron cero Enter, cero Tab, cero POST y cero productos. El control de guardado automático CUMPLE en esas muestras. La primera terminó con 32 caracteres, cuyo contenido exacto no se retuvo. La última registró primero el valor exacto 00CAT03K y terminó con 16 caracteres, confirmados por comparación como dos copias consecutivas de la etiqueta. El resultado final fue 00CAT03K00CAT03K. La hipótesis de configuración antigua en el móvil es compatible con el cambio observado tras reiniciarlo, pero no se inspeccionó el estado interno del teléfono.

HU-PROD-03/CA01 tiene evidencia de recepción física de código completo con ceros iniciales. La captura final de una única etiqueta queda PARCIAL por acumulación de lecturas. El lector se comporta como teclado y añade al campo enfocado. No se alteró la normalización de códigos para recortar repeticiones, ya que una cadena repetida podría ser un identificador legítimo.

**PROP-03K-RELECTURA, propuesta de criterio y tarea operativa.** Dado ADMIN registrando o corrigiendo un código, cuando realiza una lectura individual sobre el campo vacío o con su valor completo seleccionado, entonces debe quedar exactamente el texto de esa etiqueta. Ante repetición accidental, el operador debe poder reemplazar la captura y revisar el texto antes de guardar. Tarea pendiente de configurar y verificar el modo de lectura individual en la app móvil. Una opción de reemplazo automático en el formulario requiere definir cómo distinguir lectura de escritura manual y conservar códigos legítimos. No se implementó una deduplicación automática.

**Pruebas propuestas.** Leer una sola vez con cámara retirada después de capturar. Repetir con selección completa del valor previo. Probar dos etiquetas distintas y dos lecturas iguales. Verificar el código final, ausencia de envío, guardado expreso y rechazo atómico de código existente. HU-PROD-03/CA02, aviso inmediato de duplicado al leer, sigue previsto y pendiente de selección de implementación.

**Cursor vigente 03-K5 / PROP-03K-RELECTURA.** En la app móvil comprobar el modo individual y repetir con una sola lectura. Después comprobar reemplazo explícito seleccionando todo el campo antes de leer nuevamente. Concluir el guardado manual y consulta de la ficha entre roles en una base nueva. El funcionamiento sin Enter ya tiene dos muestras y se conserva como resultado del perfil aplicado.

Los tres servidores Django terminaron. Sus resultados confirman conservación de las bases protegidas y del XLSX. Las dos últimas bases conservaron toda la instantánea comercial, incluyendo cero productos. El programa del lector queda configurado con solo BARCODE en la plantilla existente. PostgreSQL y suite global no se repitieron, dado que este corte cambió la configuración externa y el soporte de observación. Las demás etapas mantienen su estado documentado.


[Ejecución con Enter](../evidencias/03-K-physical-20261110T180229612612Z/physical.json) · [Primera ejecución sin Enter](../evidencias/03-K-physical-20261110T180807525819Z/physical.json) · [Segunda ejecución sin Enter](../evidencias/03-K-physical-20261110T180914638365Z/physical.json).


## Continuación 03-K5 · captura individual y alta explícita

10/11/2026, 13:14–13:16 Lima. El usuario aclaró que la versión móvil ofrece cámara y un botón de captura, sin opción visible Single scan. Esta interacción es suficiente para la prueba. En la base nueva el código físico 00CAT03K llegó con ocho eventos de entrada y dos ceros iniciales. Hasta confirmar el operador hubo cero Enter, cero Tab, cero POST y cero productos. Después de la confirmación humana, el soporte de auditoría pulsó explícitamente Registrar producto, observó la página de alta y comprobó un producto persistido con el código exacto. Se verificó así la separación temporal entre captura y guardado mediante acciones normales del formulario.

ALMACENERO entró desde Catálogo de productos y vio Higiene, precio 8,50, mínimo 10, cero unidades y Sin stock vigente, sin botones de gestión. VENDEDOR entró desde Preparar venta, con turno propio abierto, y buscó el código. La ficha sin stock no se ofreció. El servidor terminó y las bases protegidas y XLSX conservaron su hash. Las capturas y los registros JSON permiten reproducir y verificar estas observaciones. El clic de guardado lo ejecutó la automatización después de confirmar la captura física el usuario.

HU-PROD-03/CA01 CUMPLE en esta muestra de captura física y alta. El control de guardado explícito CUMPLE muestra. El usuario puede tomar varias capturas del mismo código. Se acreditó anteriormente que se concatenan en el campo enfocado. Releer con el campo vacío o su texto completo seleccionado evita añadir al valor previo. El reemplazo mediante una segunda lectura física queda NO EJECUTADO. La cadena concatenada puede cumplir el formato y ser única, por lo que no debe suponerse que la validación de duplicados la detectará como error de lectura. Ese riesgo se mantiene en PROP-03K-RELECTURA.

Cursor vigente **03-K6 / PROP-03K-RELECTURA**. Definir y verificar la interacción de reemplazo ante una segunda captura, conservando códigos legítimos y entrada manual. HU-PROD-03/CA02 sigue pendiente de selección e implementación de aviso inmediato al leer. La auditoría no modificó el código de la aplicación durante este corte. La planificación conserva los 27 CA base con 21 del alcance implementado que cumplen en muestras y seis previstos, uno de estos últimos con evidencia física favorable de CA01. Los cuatro criterios suplementarios de categoría conservan su evidencia previa.


[Evidencia física y guardado](../evidencias/03-K-physical-20261110T181416503086Z/physical.json) · [Persistencia final](../evidencias/03-K-physical-20261110T181416503086Z/orm-final.json).


## Continuación 03-K6 · lecturas repetidas

10/11/2026, America/Lima. El usuario pidió repetir lecturas del mismo código y solucionar su acumulación. La cámara informó 19 lecturas en la primera prueba. El campo acumuló ocho copias y llegó a su límite de 64 caracteres. No hubo envío ni altas.

Se configuró la plantilla existente del lector con PRESS KEY Ctrl+A seguido de BARCODE. No incluye Enter. Tras reiniciar la app móvil y abrir sesión nueva, se observaron 35 eventos Ctrl+A en el campo y 35 llegadas completas del código 00CAT03K. La longitud máxima observada fue ocho caracteres. Antes de confirmar, el campo contenía exactamente el código y existían cero POST y cero productos. Después de la confirmación del usuario, el soporte pulsó Registrar y persistió una ficha con ese código. ALMACENERO la consultó sin acciones de edición y con cero existencias. VENDEDOR no la encontró entre productos ofrecidos para venta. El servidor Django terminó y las bases protegidas y XLSX conservaron sus hashes.

**PROP-03K-RELECTURA CUMPLE en esta muestra física del formulario de alta.** Cada lectura reemplazó la anterior bajo la configuración probada. El lector actúa sobre el elemento que tiene el foco y Ctrl+A selecciona su contenido completo. Por tanto, la configuración también sustituye el texto de cualquier otro campo o aplicación que esté enfocado al leer. Su uso exige enfocar el campo destinado a recibir el código. La licencia solo permitió una plantilla, por lo que el ajuste se aplicó a Output template 1 y afecta a sus demás usos. Para revertirlo se retira PRESS KEY y se guarda la plantilla.

No se probaron una segunda etiqueta diferente, edición de ficha ni un flujo de venta con el lector. El aviso inmediato de duplicados de HU-PROD-03/CA02 sigue previsto. **Cursor 03-K7 / PROP-03K-RELECTURA.** Verificar reemplazo con dos etiquetas diferentes en alta y edición, foco correcto, captura manual y rechazo final de un código existente. Después revisar el alcance del aviso inmediato de duplicado.


[Evidencia de relecturas](../evidencias/03-K-physical-20261110T182622655374Z/physical.json).
