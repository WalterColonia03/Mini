# Etapa 13 · Inventario de planificación

Fecha: 13/11/2026 (America/Lima). Pasada: **primera**. Sublote documental: clasificación completa CONF/DASH/REP y contrato del panel mínimo. Este anexo no acredita ejecución de navegador ni servidor, no cambia08 ni producto y no hereda resultados anteriores como aprobaciones actuales. La evidencia dinámica corresponde a ETAPA-13 y sus anexos.

Se leyeron completos PROTOCOLO_COMUN y CONTINUIDAD_Y_SEGUNDA_PASADA. Búsqueda desde la raíz con `rg --files -g AGENTS.md -g '*PLANIFICACION_SCRUM_R1PMV.xlsx'`: no resultados; XLSX no usado como fuente.21:36 ya registra esa ausencia. La versión de 08 inventariada tiene SHA-256 `08cc56a5843b15a238ac8bfca97bff2f6a905b36d216e65ca9f09eb7ac939dad`. Las referencias de líneas de este anexo corresponden a esa versión de entrada. El informe principal documenta el build.

## Clasificación y alcance

Las **16 HU** (2 CONF, 5 DASH, 9 REP), **39 CA base** y16 casos escritos del tramo están **PREVISTO/FUTURO**, EPIC-REP, MoSCoW **W** relativo a R1. Cada ficha exige refinamiento antes de seleccionarse. No constituyen39 incumplimientos actuales ni16 funciones entregadas. Los SP son orientativos y conservan los anteriores; no estiman trabajo restante.

**Sí está aceptado el panel mínimo**, mediante RN-06 y DEC-07-VENCIDOS-FILTRO, más RN-29 y CT-COHERENCIA-UI. Su aceptación anterior se documenta en CONSOLIDACION:9,:63–64: delegación documental12/11, ventana de 30 días rotulada, críticos solo producto/categoría activos y vencidos físicos incluidos aunque inactivos. No equivale a seleccionar DASH/REP completos ni autoriza código por existir en el archivo. La autorización de esta sesión debe interpretarse desde su instrucción, sin convertir las recomendaciones siguientes en aceptadas automáticamente.

Los actores «dueño» de las fichas futuras se corresponden con ADMIN: RN-29:4207 no crea un cuarto rol. Los permisos actuales ALMACENERO/VENDEDOR proceden de RN-29/DEC07 y no de una concesión futura general de reportes.

| HU | Fuente08 | SP | CA | Reglas / dependencias | Estado de cada CA |
|---|---:|---:|---|---|---|
| HU-CONF-01 | 3098 | 1 | 01–02 | AUTH01 | PREVISTO/FUTURO |
| HU-CONF-02 | 3142 | 3 | 01–03 | CONF01 | PREVISTO/FUTURO |
| HU-DASH-01 | 3191 | 5 | 01–03 | VEN01c | PREVISTO/FUTURO |
| HU-DASH-02 | 3240 | 3 | 01–02 | VEN01c | PREVISTO/FUTURO |
| HU-DASH-03 | 3283 | 5 | 01–03 | RN06/23;INV01a,CAJA05,PROD06 | PREVISTO/FUTURO |
| HU-DASH-04 | 3331 | 3 | 01–02 | VEN01c | PREVISTO/FUTURO |
| HU-DASH-05 | 3375 | 2 | 01–03 | SOL01 | PREVISTO/FUTURO |
| HU-REP-01 | 3423 | 5 | 01–02 | VEN01c | PREVISTO/FUTURO |
| HU-REP-02 | 3467 | 3 | 01–03 | VEN01c | PREVISTO/FUTURO |
| HU-REP-03 | 3515 | 3 | 01–02 | VEN01c | PREVISTO/FUTURO |
| HU-REP-04 | 3558 | 2 | 01–02 | VEN01c,VEN07 | PREVISTO/FUTURO |
| HU-REP-05 | 3601 | 3 | 01–03 | RN06;INV01a | PREVISTO/FUTURO |
| HU-REP-06 | 3648 | 2 | 01–02 | INV01a | PREVISTO/FUTURO |
| HU-REP-07 | 3691 | 5 | 01–03 | RN14/27/28;VEN01c,INV01a | PREVISTO/FUTURO |
| HU-REP-08 | 3740 | 3 | 01–02 | INV02 | PREVISTO/FUTURO |
| HU-REP-09 | 3783 | 3 | 01–02 | REP01/02/05/07/08 | PREVISTO/FUTURO |

## Inventario individual de criterios

Cada fila es una síntesis de un criterio de 08, no su sustitución. **Estado de ejecución de todas estas funciones completas: NO EJECUTADO** en este anexo; clasificación de alcance PREVISTO/FUTURO. Cada HU tiene `CP-<HU>-001` diseñado, no ejecutado, y aplica condiciones comunes/CT-COHERENCIA-UI.

| ID (prefijo HU-) | Fuente08 | Obligación del criterio / salida o acción |
|---|---:|---|
| CONF-01/CA-01 | 3120 | Mostrar nombre, RUC, dirección, teléfono y logo usados en constancia. |
| CONF-01/CA-02 | 3124 | Advertencia visual de datos incompletos. |
| CONF-02/CA-01 | 3164 | Actualización de datos aparece en nuevas constancias. |
| CONF-02/CA-02 | 3168 | Logo cargado aparece en constancia y pantalla principal. |
| CONF-02/CA-03 | 3172 | No definir series oficiales; constancia sin validez tributaria. |
| DASH-01/CA-01 | 3213 | Ventas totales S/, número y ticket promedio del día. |
| DASH-01/CA-02 | 3217 | Nueva venta confirmada recalcula/muestra indicadores. |
| DASH-01/CA-03 | 3221 | Hoy/semana desde lunes/mes desde día 1; Lima; rango visible hasta instante de consulta, sin futuro. |
| DASH-02/CA-01 | 3262 | Gráfico monto por día del período. |
| DASH-02/CA-02 | 3266 | Día sin ventas se representa con 0. |
| DASH-03/CA-01 | 3305 | Alerta crítico muestra producto y unidades, mínimo configurable de 10 por defecto. |
| DASH-03/CA-02 | 3309 | Próximos 7 días muestra lote y días restantes. |
| DASH-03/CA-03 | 3313 | Turno sin operaciones durante 2 horas o más muestra alerta informativa. |
| DASH-04/CA-01 | 3353 | Los 5 primeros por unidades del período. |
| DASH-04/CA-02 | 3357 | Vacío literal «Sin ventas registradas en este período». |
| DASH-05/CA-01 | 3397 | Solicitud pendiente muestra producto, cantidad, solicitante y fecha. |
| DASH-05/CA-02 | 3401 | Selección conduce a aprobación/rechazo. |
| DASH-05/CA-03 | 3405 | Vacío literal «Sin solicitudes pendientes». |
| REP-01/CA-01 | 3445 | Rango fechas; filas fecha, número, medio, base, IGV y total. |
| REP-01/CA-02 | 3449 | Filtro efectivo/Yape limita operaciones y suma. |
| REP-02/CA-01 | 3489 | Ranking por unidades e importe del rango. |
| REP-02/CA-02 | 3493 | Porcentaje de participación sobre ventas del período. |
| REP-02/CA-03 | 3497 | Orden por encabezados unidades/monto. |
| REP-03/CA-01 | 3537 | Fila por día con monto y operaciones. |
| REP-03/CA-02 | 3541 | Día sin venta incluido con 0. |
| REP-04/CA-01 | 3580 | Totales efectivo y Yape separados en período. |
| REP-04/CA-02 | 3584 | Filtro por fechas limita los montos al rango. |
| REP-05/CA-01 | 3623 | Lista stock disponible<=mínimo configurable de 10 por defecto. |
| REP-05/CA-02 | 3627 | Muestra stock, mínimo, categoría y unidad. |
| REP-05/CA-03 | 3631 | Cero destacado «Agotado». |
| REP-06/CA-01 | 3670 | Todos los productos con stock, mínimo y estado normal/crítico. |
| REP-06/CA-02 | 3674 | Búsqueda por nombre limita resultados. |
| REP-07/CA-01 | 3713 | Ingreso neto, costo histórico comparable, ganancia comercial; exclusiones explícitas sin margen ficticio. |
| REP-07/CA-02 | 3717 | Margen=ganancia/ingreso neto×100; denominador/cobertura; cero o faltantes No calculable; no rentabilidad neta ni certificación fiscal. |
| REP-07/CA-03 | 3721 | Filtros de categoría y fechas; margen y ganancia del lapso. |
| REP-08/CA-01 | 3762 | Bajas por vencimiento, daño/rotura y robo/faltante del período. |
| REP-08/CA-02 | 3766 | Filtro por fechas limita bajas. |
| REP-09/CA-01 | 3805 | PDF con datos/filtros consultados. |
| REP-09/CA-02 | 3809 | PDF vacío indica sin datos, sin error. |

No se fabrica pantalla o reporte vacío para dar por probado un criterio futuro. El vacío del resumen actual se compara con las consultas reales, no con los literales de ranking/solicitudes todavía futuros.

## Contratos vigentes aplicables al panel

| Referencia inicial en 08 | Obligación y aplicación en esta etapa |
|---|---|
| RN-06, líneas 3938–3940 | Mínimo configurable entre 0 y 999999, con 10 por defecto. El crítico se calcula con stock vendible igual o inferior al mínimo para producto y categoría activos. Los vencidos físicos se muestran aunque estén inactivos. |
| DEC-07-VENCIDOS-FILTRO, línea 4783 | Día de Lima, ventana rotulada de 30 días y turnos según rol. Próximos: hoy < fecha ≤ hoy + días. Vencidos: fecha ≤ hoy y saldo físico positivo. |
| DEC-07/C-01, línea 4787 | Identificar el vencido inactivo como no vendible. Mantenerlo fuera de los alertas de reposición. La reactivación de categoría pertenece a las dependencias 03/07. |
| DEC-07/C-02, líneas 4791–4793 | En la consulta enlazada se admiten días enteros ASCII de 1 a 3650, por defecto 30. Valor inválido recibe mensaje y usa 30. Etiqueta, conteo y lista corresponden al mismo filtro. |
| DEC-07/C-03, línea 4797 | El resumen diario conserva su significado frente a las HUs futuras de período, margen, gráfico, ranking y solicitudes. La decisión sobre un índice parcial requiere medición de volumen. |
| RN-29, líneas 4207–4224 | ADMIN consulta ventas y turnos globales. ALMACENERO consulta inventario. VENDEDOR tiene acceso a sus propios turnos, ventas y POS. El servidor verifica la autorización de las consultas directas. |
| HU-AUTH-01/CA-01 y CA-04, líneas 75 y 87 | La sesión conduce a operaciones autorizadas. La operación ajena se deniega sin datos protegidos ni cambios de negocio. |
| DEC-12-PERMISOS-HISTORIAL-Y-MENU/C-02, línea 4507 | Reconciliar menú y permiso en servidor por rol, incluyendo revocación y ausencia de acciones de operar turno en ADMIN. |
| CT-COHERENCIA-UI/C-01, línea 4994 | Éxito tras confirmación y rechazo sin mutación. CP-VISIBLE-001. |
| CT-COHERENCIA-UI/C-02, línea 5011 | Identificar unidad y conjunto de la consulta. Distinguir físico de vendible, total del filtro de total de página y consulta vacía de consulta fallida. CP-VISIBLE-002. |
| CT-COHERENCIA-UI/C-03, línea 5028 | Hacer corresponder menú y autorización. Identificar funciones futuras y evitar ofrecerlas como implementadas. CP-VISIBLE-003. |
| CT-COHERENCIA-UI/C-04, línea 5045 | Inventariar superficies dinámicas, evidencias por caso y estados pendientes. CP-VISIBLE-004. |
| RN-23, línea 4131 | La detección de inactividad durante 2 horas para revisión y cierre es futura. El conteo actual se refiere a turnos en estado abierto. |
| RN-02, línea 3888 y HU-VEN-07 | Yape futuro requiere comprobación humana y código único. |
| RN-14/27/28, líneas 3846, 3859–3860 y 4197 | Un margen comercial futuro requiere costo histórico comparable y cobertura explícita de datos. La política fiscal aplicable permanece en investigación. |

## Contraste de documentos al iniciar el sublote

| Fuente | Líneas | Resultado |
|---|---|---|
| 01 | 10, 14, 24, 30 | Una caja, efectivo, productos en unidades con vencimiento y tres roles. 33 HU seleccionadas y 41 futuras. Delegación documental y fuente funcional única en 08. |
| 21 | 10, 26, 36 | Recoge selección, límites de la evidencia anterior y ausencia del XLSX. La etapa 13 figuraba pendiente al inicio. |
| 09 | 53–54, 61–74 | Las 16 filas CONF/DASH/REP tienen prioridad W. |
| 03 | 192–230, 274–276, 375–390, 404 | 39 CA futuros y tres criterios del contrato DEC-07. Sus casos escritos tienen estado de diseño en la versión de entrada. |
| 07 | 14, 31, 64, 116, 373 | Vista de RN-06/23, Yape y costo concordante con 08 en los fragmentos consultados. |
| 02 | 16–18, 32, 36–40, 73–75 | GET de consulta conserva datos de negocio. El servidor decide permisos y cálculos. Dinero Decimal con dos posiciones, costo con cuatro. UTC para persistencia y Lima para el negocio. |
| 02, NFR | 158–162, 166 | NFR-03 permisos, NFR-04 dinero, NFR-05 búsqueda y cobro, NFR-06 teclado, NFR-07 Chrome a 1366×768 y NFR-11 fechas de Lima. El diseño no asigna al panel el umbral de búsqueda de dos segundos. |
| 02, DT | 211–225 | DT-01 web interna, DT-02 monolito, DT-03 motor objetivo PG17, DT-04 roles, DT-08 decimales, DT-10 caja única y DT-15 volumen de referencia de 2000 productos, 20000 lotes y 300 ventas por día. |
| 14 | 14–22, 32 | La definición de Hecho requiere evidencia por rol en navegador. Las 41 HU futuras conservan su selección fuera de R1. |
| 16 | 18, 28–29, 32, 38, 44 | Trabajos DEC-12-PERMISOS, DEC-12-ORDEN, DEC-07-VENCIDOS-FILTRO, DOC-00-01 y CT-COHERENCIA-UI. Para DEC-07 ya se pedían medianoche de Lima, inactivos, etiquetas y conteos. |
| CONTROL_SPRINTS | 8–10 | Fechas de S1/S2/S3 y conteos de pruebas conservan su carácter histórico. |
| CONSOLIDACION | 9, 63–64 | Se aceptó el panel mínimo de 30 días por delegación el 12/11. |

## Observaciones iniciales y tratamiento

La versión de entrada de `identity/views.py` (líneas 231–264) calculaba ventas diarias, descuentos, turnos abiertos y conteos de productos y lotes. La anotación «HUECO-08 / HU-REP-01» atribuía la función al reporte de período. La referencia aplicable es DEC-07-VENCIDOS-FILTRO. La plantilla previa (líneas 16–35) presentaba siete cifras para ADMIN y tres para ALMACENERO bajo «Resumen del negocio — hoy». Las ventas corresponden al día, mientras que los turnos y el inventario describen el estado al consultar. El grupo ofrece enlaces de inventario, vencimientos e historial. Su destino y el filtro con el que abre son observables en la evidencia de navegador.

Se aplicó la parte ya respaldada por RN-06, RN-29, DEC-07 y CT-COHERENCIA-UI. El alcance documental aceptado incluye expresar la fecha de Lima y la recarga, diferenciar el estado actual de las ventas del día y limitar el contexto del servidor al rol. El caso CP-DEC-07-VENCIDOS-FILTRO-002 conserva estos controles y los datos del sublote. El informe principal registra por separado el build, la corrección y las revalidaciones alcanzadas. [Informe y cursor de ejecución](../ETAPA-13.md).

## Recomendaciones pendientes de decisión o medición

| Necesidad y actor | Alternativas y beneficio | Riesgo, costo y dependencias | Prueba y aceptación |
|---|---|---|---|
| ADMIN necesita cifras compatibles si se produce una venta simultánea o cambia el día de Lima durante las consultas. | Obtener suma y conteo de ventas en una agregación y usar una fecha común. Si se requiere consistencia entre tablas, evaluar una instantánea consistente. | Costo bajo para agregación y mayor para una transacción amplia. Esta última puede aumentar la carga. Afecta al diseño de consultas y NFR-11. | Introducir una escritura entre lecturas en una base aislada y probar la medianoche de Lima. Se requiere evidencia específica para declarar consistencia bajo concurrencia. |
| ADMIN y ALMACENERO necesitan identificar el conjunto de registros tras cada cifra. | Ofrecer un enlace filtrado o rotular el enlace como consulta general y presentar su filtro visible al abrir. | Costo bajo a medio según los filtros ya existentes. Un filtro diferente puede inducir a conciliar montos incompatibles. Depende de consultas de las etapas 07 y 12. | Comparar tres filas del conjunto con la cifra, comprobar retorno y permisos. La apertura sin filtro del historial es una observación de la muestra. La elección de navegación sigue abierta. |
| Usuarios del panel necesitan tiempos de respuesta compatibles con su operación. | Medir la consulta existente en el volumen DT-15. Seleccionar índices o agregados persistidos solo con evidencia del costo. | Medición de costo bajo. Optimización de costo medio, con riesgo de datos viejos si se introduce caché. Se desconoce el volumen real. | Registrar host, versiones, distribución, tiempos y p95. Definir umbral propio del panel si el responsable lo necesita. |
| ADMIN necesita requisitos refinados antes de seleccionar los reportes. | Aprovechar DASH-01, REP-02, REP-07, REP-09 y CONF-02 existentes para delimitar actualización, participación, cobertura de costos, exportación y logo histórico. | Costo variable según HU. Un costo sin base comparable puede producir un margen engañoso. Requiere hechos del negocio y decisión de selección. | Precisar latencia máxima, desempate o denominador según caso, tratamiento del costo y límites de archivos. Los 39 CA permanecen clasificados como futuros. |

**Continuidad documental.** Se inventariaron 16 HU y 39 CA futuros. La matriz de las pruebas aplicables al panel conserva su estado por caso y build. El cursor de ejecución vigente se mantiene en [ETAPA-13](../ETAPA-13.md).
