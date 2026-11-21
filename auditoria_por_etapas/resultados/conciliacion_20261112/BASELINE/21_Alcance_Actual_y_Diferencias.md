# Guía de alcance actual y diferencias identificadas

**Corte de revisión documental: 5 de noviembre de 2026.** Jira dejó de usarse y no forma parte de la evaluación. Las menciones a Jira y los cronogramas de octubre se conservan como historia, sin exigir cuentas, tableros, carga de incidencias ni registro de horas en esa herramienta.

Los documentos de reglas e historias describen el producto deseado, incluidas funciones futuras. Una historia o una marca histórica de “completada” no demuestra por sí sola que todos sus criterios se cumplan. Esta guía recoge diferencias comprobadas mediante lectura del código y documentos; no sustituye pruebas integrales de todas las pantallas, roles, campos y escenarios, ni declara conformidad total.

## Recorrido disponible por rol

| Rol | Acciones visibles en código | Límites de acceso |
|---|---|---|
| Administrador | Gestión de empleados, categorías, productos y proveedores; consulta de stock, movimientos, vencimientos, ventas y turnos; registro de mermas y ajustes físicos. | No abre caja ni cobra. Puede consultar constancias de ventas. |
| Almacenero | Consulta de productos, proveedores, stock, movimientos y vencimientos; registra carga inicial, entradas posteriores y mermas. | No gestiona empleados, categorías, productos ni proveedores; no registra ajustes físicos ni cobra. |
| Vendedor | Abre y cierra su turno, prepara y cobra ventas en efectivo, consulta sus ventas y constancias. | No gestiona catálogo, empleados ni inventario; su historial de ventas se limita a sus propias ventas. |

Los permisos detallados están en los decoradores de las vistas y las restricciones adicionales en los servicios. Los formularios, el stock y los turnos deben verificarse con datos de prueba de cada rol; esta tabla describe el acceso previsto en código, no una certificación de seguridad.

Un recorrido de demostración consiste en que el administrador registre el producto y el proveedor, el almacenero registre la carga por lotes, y el vendedor abra su turno y cobre en efectivo. Después el administrador o almacenero puede comprobar stock y movimientos; el vendedor puede cerrar su turno. La constancia es **solo de control interno**: no es una boleta ni factura tributaria. El negocio debe emitir el comprobante correspondiente por un sistema o canal autorizado externo. El software no integra SUNAT ni pagos digitales, por lo que no debe presentarse como solución tributaria completa.

## Discrepancias que requieren cierre

| Referencia de planificación | Situación observada | Estado |
|---|---|---|
| RN-17 y HU-AUTH-02, bloqueo de cuenta 15 minutos | El ingreso de la aplicación bloquea durante 15 minutos el identificador normalizado tras cinco fallos; el bloqueo se comparte entre sesiones y muestra el tiempo restante. Es necesario aplicar la migración `identity.0005`. | Cubierto por pruebas de identidad en SQLite; falta comprobar concurrencia en PostgreSQL y protección adicional de tráfico. El acceso independiente `/admin/` no usa este control. |
| HU-VEN-01a, bloqueo de pantalla tras cinco minutos | La historia requiere bloquear la pantalla y pedir la contraseña conservando la venta. El registro histórico de sprints confundía este ID con la preparación de la venta, que corresponde a HU-VEN-01b. | **Pendiente de implementar o revisar alcance**; no afirmar que se bloquea por inactividad. |
| HU-VEN-03, comprobante PDF o correo | Es una idea fuera del alcance en el backlog. El registro de sprints usaba erróneamente ese ID para descuentos. | PDF/correo oficiales no implementados; descuento disponible sin ID de historia validado. |
| HU-INV-04, movimientos; HU-INV-05, historial de bajas; HU-INV-06, historial de ajustes | El registro histórico asignaba estos IDs a otras funciones. Existe una pantalla de movimientos por producto, pero la historia HU-INV-04 también pide saldo resultante, filtros y referencia de reposición; no se ha acreditado su cumplimiento íntegro. | Identificadores corregidos en el control de sprints; criterios pendientes de comprobación o implementación. |
| HU-REP-01, reporte analítico por período y medio de pago | Existe un resumen diario en el panel, pero no demuestra el reporte por rango ni el filtro de Yape especificados en la historia. | **No presentar el panel como HU-REP-01 completa.** |
| HU-VEN-05b, filtros de historial | La historia pide rango de fechas, vendedor y turno; la vista consultada expone filtros de fecha y correlativo. | **Parcial**, faltan los filtros requeridos o la decisión de cambiar el requisito. |
| Diseño histórico 02, permisos de constancias | El diseño original reservaba la constancia al vendedor; el código permite al administrador verla y restringe al vendedor a sus ventas. | Matriz de diseño actualizada para reflejar el acceso observado. |

La ausencia de una diferencia en esta tabla no acredita que el criterio esté cumplido. Las correcciones posteriores deben acompañarse de revisión del comportamiento, roles y pruebas, y reflejarse tanto en los documentos como en el sistema.

## Evidencia y preparación de una exposición

1. Iniciar el sistema con cuentas ficticias y datos de prueba, usando las instrucciones de `r1-pmv/README.md`.
2. Recorrer las operaciones con cada cuenta; comprobar resultados, datos guardados, accesos directos denegados y los efectos entre roles. No utilizar datos reales de clientes ni contraseñas reales para la demostración.
3. Ejecutar las comprobaciones disponibles indicadas en el README y conservar el resultado con fecha y entorno. Las cifras de pruebas de reportes anteriores son históricas.
4. Mostrar expresamente las diferencias pendientes de esta guía y las funciones futuras como tales. La preparación comercial, cumplimiento legal integral y seguridad de un despliegue real requieren validación adicional específica; esta revisión no constituye una certificación.

## Verificación de esta revisión

El 5 de noviembre de 2026 se ejecutaron `manage.py check`, `makemigrations --check --dry-run` y `manage.py test --noinput` con `APP_ENV=test` y SQLite: 191 pruebas aprobadas, sin cambios de modelo pendientes. Se aplicó `identity.0005_loginattempt` en la base SQLite local de demostración; otras instalaciones deben aplicar sus propias migraciones. No se ejecutó una prueba de concurrencia sobre PostgreSQL porque no había servidor disponible. Estas pruebas no acreditan el cumplimiento de todos los criterios ni un recorrido visual completo de todas las pantallas.

> **Complemento de auditoría · 09/11/2026.** El cierre incorpora Chrome, bloqueo con espera real y cuatro escenarios de ingreso concurrente en PostgreSQL. Tráfico, retención, administración y observabilidad conservan hallazgos abiertos. [Resultados de etapa 01](auditoria_por_etapas/resultados/ETAPA-01.md) · [Decisiones y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-01-cierre-y-traspaso.md)

## Alcance actual de catálogo aceptado · 09/11/2026

**DOC03-01 resuelto por decisión explícita del usuario:** «Productos de cualquier categoría, por unidad y con vencimiento obligatorio». Se puede registrar en cualquier categoría activa. El formulario informa UND y vencimiento obligatorio; inactivas/inexistentes se rechazan. La preparación histórica «Productos enlatados» deja de limitar el catálogo actual. Productos por peso o sin vencimiento, edición/eliminación comercial de categorías y escáner permanecen fuera de esta ampliación.

**DOC-00-14 conciliado con el pedido original:** ADMIN gestiona; ALMACENERO consulta catálogo; VENDEDOR consulta en venta autorizada. Se actualizó HU-PROD-01 sin ampliar permisos. La referencia previa «administrador o vendedor» se conserva en el registro histórico de la decisión. Siguen pendientes código editable (DOC03-02), política de homónimos y máximo del stock mínimo. [Decisiones, criterios y evidencia03-F](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md) · [Estado de la auditoría03](auditoria_por_etapas/resultados/ETAPA-03.md).

**DOC03-02 resuelto por decisión del usuario (09/11/2026):** el ADMIN puede corregir un código si es único y conserva los históricos. Se actualizó HU-PROD-04/CA03 para conciliar el agregadoQA08:872 y la funcionalidad existente. Barcode to PC Server es la solución prevista de captura, sin prueba física ejecutada ni aprobación automática de HU-PROD-03. Homónimos y máximo del mínimo continúan abiertos. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-G-codigo-y-lector.md).


## Decisiones aplicadas · catálogo03-I · 10/11/2026

PROP-03C-LIMITES y PROP-03C-NOMBRE aceptadas: mínimo entero0..999999 (alta omitida10) y nombres globalmente únicos ignorando mayúsculas/espacios redundantes, incluso inactivos. Presentaciones diferentes deben identificarse en el nombre. Se mantienen acentos y equivalencia NFC. La aceptación «bien, continua» responde a esas dos recomendaciones; no autoriza otras ampliaciones.

Verificado en aislado: validación y CHECK de máximo, clave normalizada UNIQUE, errores de campo con rollback y migración0005 con examen previo de conflictos. Base original revisada solo en lectura, sin conflictos en5 productos; no migrada. Pendientes: despliegue0003/0004/0005, lector físico/aviso inmediato y propuestas de estados/categorías. Los párrafos anteriores conservan sus cortes históricos y no reabren decisiones resueltas.

[Evidencia y límites03-I](auditoria_por_etapas/resultados/anexos/ETAPA-03-I-politicas.md).


## Confirmación de estado de categoría · 10/11/2026

Decisión del usuario aplicada al catálogo comercial. ADMIN revisa los efectos antes de activar o desactivar. Una pantalla antigua se rechaza con indicación de revisar el estado vigente si otra confirmación cambió la categoría. El alcance aceptado se registra con PROP-E00-HU-02 y los cuatro criterios suplementarios de 08. El cambio de estado conserva las fichas y las ventas históricas. La migración 0006 está probada en entornos aislados y pendiente de despliegue real.

[Auditoría 03-J](auditoria_por_etapas/resultados/anexos/ETAPA-03-J-estado-categoria.md).

## Reactivación y venta en mostrador · 10/11/2026

La reactivación de una ficha conserva su precio, sus lotes y sus referencias históricas. Para que el vendedor con turno propio abierto la encuentre en mostrador debe tener categoría activa y unidades disponibles en lotes que venzan después de hoy en Lima. El catálogo distingue «Disponible», «Sin stock vigente» y «Categoría desactivada». El usuario aceptó esta precisión en HU-PROD-05/CA02. [Etapa 03, corte K](auditoria_por_etapas/resultados/ETAPA-03.md#etapa-03-k).

**Catálogo, corte 03-K9 del 10/11/2026.** En el entorno aislado se verificaron el rechazo de cambios incompatibles desde una ficha antigua y la captura opcional para ADMIN en alta y edición. El operador comprobó dos etiquetas físicas con Barcode to PC. La detección de duplicado acreditada se produce al guardar. La advertencia inmediata de HU-PROD-03/CA02 sigue prevista. Para recepción multiproducto y retiros por lote se documentaron propuestas y pruebas pendientes. [Informe de catálogo](auditoria_por_etapas/resultados/ETAPA-03.md) · [Traspaso de recepción y retiros](auditoria_por_etapas/resultados/anexos/ETAPA-03-recepcion-y-retiros-pendientes.md).


**Corte03-O,10/11/2026, selección vigente:** por instrucción de aplicar las mejoras pendientes se incorpora HU-PROD-03/CA02. ADMIN recibe aviso de código duplicado al leer o escribir en alta/edición, incluidas fichas inactivas; la propia ficha se excluye al editar. El diálogo protege otros campos y exige copiar/guardar expresamente. Ante fallo de consulta se informa y se conserva la validación final del servidor. Captura físicaK9 y pruebas softwareO tienen evidencias separadas; aviso físico nuevo pendiente. No modifica estados históricos de R1. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-N-O-reclasificacion-y-duplicados.md).


**Corte03-P,10/11/2026:** HU-PROD-03/CA02 verificado también con teléfono del operador en cinco fases (34 lecturas,52 comprobaciones). Existente/inactivo y ajeno bloquean la copia; propio permite; cero guardados automáticos. Migraciones0003–0006 ensayadas solo en copia nueva de la base conservada; despliegue real pendiente. [Evidencia y límites](auditoria_por_etapas/resultados/anexos/ETAPA-03-P-aviso-fisico-y-migraciones.md).


**Conciliación03-W,10/11/2026:** las adendas fechadas anteriores conservan su corte; PROD03 fue seleccionado en O y su aviso físico se verificó en P. Persiste la diferencia literal entre CA01 original y el flujo aceptado de copia expresa. La matriz actual y los pendientes de alcance, EAN/UPC, despliegue y recepción/retiros están en [03-W](auditoria_por_etapas/resultados/anexos/ETAPA-03-W-conciliacion.md).

**Actualización03-X,11/11/2026 (ejecución10/11):** PROD03/CA02 queda PARCIAL en la frontera EAN13/UPC12: seis lecturas físicas recibieron12 dígitos ante una ficha almacenada con13 y el aviso no indicó duplicado. La unicidad literal conserva sus muestras favorables.69/69 controles navegador/HTTP/ORM,16/16 servicio/DB y9/9 observación física; estos últimos acreditan la observación, no la equivalencia. DEC-03X-IDENTIDAD y PROP-03X-CA01..03/T01..03 son propuestas pendientes, sin cambio funcional, fusión ni migración. No se modifican estimaciones/sprints históricos ni se aprueban otras etapas. [Evidencia, alternativas y criterios](auditoria_por_etapas/resultados/anexos/ETAPA-03-X-codigos-ean-upc.md).

**Actualización 03-Y · 11/11/2026.** Decisión vigente: GTIN de artículos unitarios (12/13 dígitos y representación de 14 con cero inicial) o código interno elegido por ADMIN. Las fichas previas siguen sin clasificar. Los indicadores de embalaje y la conversión caja/unidad quedan fuera de esta implementación. [Evidencia 03-Y](auditoria_por_etapas/resultados/anexos/ETAPA-03-Y-identidad.md).
