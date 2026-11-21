# Barcode to PC Server · Incorporación prevista y pruebas pendientes

09/11/2026, America/Lima. El usuario indicó Barcode to PC Server como solución de lectura. Este documento concreta esa elección dentro de HU-PROD-03; no certifica una integración ejecutada con teléfono o servidor real. No se instaló ni configuró software de terceros en esta sesión.

## Mecanismo documentado y configuración propuesta

La documentación oficial describe captura móvil y escritura en el campo que tenga el foco en el PC mediante emulación de teclado. La inferencia para este proyecto es usar el campo «Código de barras» existente, sin necesitar una API del lector dentro de Django. [Keyboard Emulation](https://docs.barcodetopc.com/keyboard-emulation/), consultado09/11/2026.

Las plantillas de salida componen los datos y acciones enviados. Para registrar/editar productos propongo un perfil que envíe solo el código y, si se necesita terminar el campo, Tab; el operador revisa la ficha y pulsa Guardar. Es una propuesta de configuración para este proyecto, no una configuración ya observada. [Output Templates](https://docs.barcodetopc.com/output-template/how-it-works/).

El componente ENTER emula esa tecla y puede enviar un formulario. Por ello, un perfil que incluya Enter exige comprobar su efecto antes de usarlo en alta/edición; la propuesta inicial evita el envío automático. [Componente ENTER](https://docs.barcodetopc.com/output-template/components/enter/).

Flujo previsto: ADMIN abre Registrar producto o Editar; coloca el foco en Código de barras y reemplaza el valor anterior cuando corresponde; lee desde la aplicación móvil conectada al servidor; revisa el código completo y el resto de campos; guarda. Las restricciones de servidor siguen siendo las mismas para lectura y digitación: texto hasta64, letras ASCII/números/espacios/guiones, clave normalizada única, sin pérdida de ceros iniciales. En edición se conservan UUID e históricos según DOC03-02. El foco inicial actual es Nombre, por lo que el foco en Código es una precondición explícita, no detección automática del lector.

No está definido un formato exclusivo EAN/UPC ni un dígito de control en las HU actuales. Elegir Barcode to PC Server no autoriza restringir los códigos alfanuméricos existentes. La red local, versiones de servidor/app, sistema móvil, simbologías y perfil concreto deben registrarse en la prueba real.

## Clasificación de HU-PROD-03 y propuesta de trabajo

| Elemento | Estado real al corte03-G | Trabajo necesario |
|---|---|---|
| CA01,08:231: código llenado al leer | PREVISTO/FUTURO de incorporación; tecnología elegida. Teclado simulado conserva0012345678905, pero no prueba teléfono/servidor/red | Ejecutar la cadena real móvil→servidor→campo, registrar versión/perfil/foco/resultado |
| CA02,08:232: aviso inmediato de duplicado al leer | PREVISTO/FUTURO; el formulario actual valida al guardar. Enviar DUPLICADO por teclado y salir del campo no mostró aviso inmediato | Definir fin de lectura (Tab u otro evento), consulta de duplicado y mensaje exacto; mantener validación final atómica |
| Edición administrativa | Aceptada por usuario en DOC03-02, implementada y verificada en muestra03-G | No depende del lector; mantener histórico y permisos para cualquier entrada |
| Campo requerido/longitud/caracteres/código único | Implementados en formulario y servidor, pruebas03-C/F/G | Escáner no debe saltar estas validaciones |

No se reclasifica la captura de teclado como scanner aprobado ni el error al guardar como detección de lectura. La elección de tecnología queda registrada, sin asignación retroactiva de sprint o puntos. Si se selecciona HU-PROD-03 para entrega actual, sus dos criterios pasarán a seleccionados pendientes y deberá ejecutarse el trabajo siguiente.

**Tareas propuestas, sin nueva HU duplicada:**

- **PROP-03G-SCAN-T01:** registrar app/servidor/dispositivo/perfil, código de terminación y manejo del foco. Preparar un perfil de alta/edición que no guarde inesperadamente.
- **PROP-03G-SCAN-T02:** diseñar y aplicar la advertencia de duplicado al finalizar lectura, mensaje «El código de barras ya está registrado», únicamente con autorizaciónADMIN, excluyendo la propia ficha al editar y manteniendo la unicidad al guardar. El contrato no presupone identificar un teclado físico frente al lector por velocidad.
- **PROP-03G-SCAN-T03:** definir repetición y sustitución de campo: reemplazar un código seleccionado, evitar concatenar dos lecturas por accidente y mostrar rechazo completo para longitud/caracteres inválidos. Sin truncar silenciosamente un código largo hasta volverlo distinto.

**Criterios propuestos de incorporación:** Dado ADMIN con campoCódigo enfocado, cuando llega una lectura completa permitida, entonces se muestra el texto completo con sus ceros iniciales y no se guarda hasta confirmar. Dado código de otra ficha, cuando termina la lectura, entonces aparece el aviso exacto y guardar sigue rechazando sin cambios. Dado un código propio en edición, cuando se verifica, entonces no se informa duplicado de sí mismo. Dado rol no autorizado, cuando solicita validación o alta/edición, entonces se deniega sin revelar fichas administrativas ni escribir.

## Pruebas reproducibles pendientes del lector real

1. Preparar base marcada nueva y ADMIN ficticio. Registrar versiones del servidor Windows, app móvil, dispositivo y plantilla elegida. Emparejar usando la configuración propia del producto; no registrar contraseñas ni QR de sesión en evidencias públicas.
2. En Alta, enfocar Código vacío y leer un código de prueba con ceros iniciales; comprobar texto exacto y ausencia de envío automático. Repetir con alfanumérico permitido.
3. Leer un duplicado existente; comprobar aviso al terminar lectura y rechazo al guardar. Repetir dos altas concurrentes: una única fila y un rechazo. Esta carrera se evalúa en PostgreSQL.
4. En Editar, reemplazar el valor seleccionado; guardar uno nuevo único y comprobar consulta nueva, UUID estable y constancia anterior intacta. Código propio debe admitirse y código de otra ficha rechazarse.
5. Probar lectura repetida, foco en otra entrada, desconexión/reconexión, 65 caracteres y carácter no permitido, prefijos/sufijos y Enter accidental. Comprobar sin truncamiento ni guardado inesperado.
6. Repetir permisos de ALMACENERO/VENDEDOR por solicitud directa. Registrar resultados esperados/observados por separado: una observación no ejecutada no se transforma en PASS.

La simulación03-G G01/G02 únicamente verifica la recepción de teclado en Chrome y reproduce la falta de aviso en blur; sus detalles se enlazan desde [código y lector](ETAPA-03-G-codigo-y-lector.md). No completa ninguna prueba física de esta lista.

## Actualización del 10/11/2026

Se ejecutaron dos intentos físicos. El historial móvil mostró las lecturas y el formulario quedó vacío. El PC mostró cero dispositivos vinculados y el teléfono informó que no podía acceder al servidor. El próximo control usa Code 128 para comprobar el texto literal después de vincular. [Evidencia y cursor 03-K2](ETAPA-03-K-lector-y-reactivacion.md).


## Continuación 03-K2

El 10/11/2026 a las 12:58 Lima, después de que el usuario informó la conexión, la lectura física Code 128 llegó al campo ADMIN como 00CAT03K, con ocho eventos de entrada y ambos ceros iniciales. Se observó inmediatamente Enter, envío POST y navegación a la ficha registrada. La base aislada guardó exactamente un producto con ese código, precio 8.50, mínimo 10, UND y vencimiento obligatorio. HU-PROD-03/CA01 CUMPLE en esta muestra física. La propuesta de revisar antes de guardar queda pendiente de ajustar el perfil de salida. El perfil interno del lector y sus versiones después de la reconexión no se inspeccionaron. La prueba acredita el resultado de extremo a extremo en navegador y persistencia, con conexión informada por el operador. El servidor Django finalizó y todos los archivos protegidos conservaron sus hashes.

**Cursor 03-K3 / PROP-03G-SCAN-T01.** Configurar la salida del lector para enviar el código sin Enter y repetir una lectura física en alta nueva, verificando campo exacto, cero POST y cero productos hasta pulsar Registrar. Después abordar el aviso inmediato de duplicado de HU-PROD-03/CA02, que sigue previsto.


**Actualización 03-K4.** Perfil BARCODE sin Enter verificado en dos muestras. La lectura final acumuló dos copias del código. Cursor 03-K5 / PROP-03K-RELECTURA. [Resultados y propuesta](ETAPA-03-K4-perfil-y-relectura.md).


## Continuación 03-K5 · captura individual y alta explícita

10/11/2026, 13:14–13:16 Lima. El usuario aclaró que la versión móvil ofrece cámara y un botón de captura, sin opción visible Single scan. Esta interacción es suficiente para la prueba. En la base nueva el código físico 00CAT03K llegó con ocho eventos de entrada y dos ceros iniciales. Hasta confirmar el operador hubo cero Enter, cero Tab, cero POST y cero productos. Después de la confirmación humana, el soporte de auditoría pulsó explícitamente Registrar producto, observó la página de alta y comprobó un producto persistido con el código exacto. Se verificó así la separación temporal entre captura y guardado mediante acciones normales del formulario.

ALMACENERO entró desde Catálogo de productos y vio Higiene, precio 8,50, mínimo 10, cero unidades y Sin stock vigente, sin botones de gestión. VENDEDOR entró desde Preparar venta, con turno propio abierto, y buscó el código. La ficha sin stock no se ofreció. El servidor terminó y las bases protegidas y XLSX conservaron su hash. Las capturas y los registros JSON permiten reproducir y verificar estas observaciones. El clic de guardado lo ejecutó la automatización después de confirmar la captura física el usuario.

HU-PROD-03/CA01 CUMPLE en esta muestra de captura física y alta. El control de guardado explícito CUMPLE muestra. El usuario puede tomar varias capturas del mismo código. Se acreditó anteriormente que se concatenan en el campo enfocado. Releer con el campo vacío o su texto completo seleccionado evita añadir al valor previo. El reemplazo mediante una segunda lectura física queda NO EJECUTADO. La cadena concatenada puede cumplir el formato y ser única, por lo que no debe suponerse que la validación de duplicados la detectará como error de lectura. Ese riesgo se mantiene en PROP-03K-RELECTURA.

Cursor vigente **03-K6 / PROP-03K-RELECTURA**. Definir y verificar la interacción de reemplazo ante una segunda captura, conservando códigos legítimos y entrada manual. HU-PROD-03/CA02 sigue pendiente de selección e implementación de aviso inmediato al leer. La auditoría no modificó el código de la aplicación durante este corte. La planificación conserva los 27 CA base con 21 del alcance implementado que cumplen en muestras y seis previstos, uno de estos últimos con evidencia física favorable de CA01. Los cuatro criterios suplementarios de categoría conservan su evidencia previa.


[Evidencia física y guardado](../evidencias/03-K-physical-20261110T181416503086Z/physical.json) · [Persistencia final](../evidencias/03-K-physical-20261110T181416503086Z/orm-final.json).
