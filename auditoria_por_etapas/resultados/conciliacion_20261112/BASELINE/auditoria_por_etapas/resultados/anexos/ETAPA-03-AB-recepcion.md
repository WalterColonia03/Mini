# 03-AB · Recepción consecutiva de productos y repetición de operaciones

11 de noviembre de 2026, America/Lima. Continuación de PROP-03-RET-T01 desde 03-AA, con comprobaciones pertenecientes a las etapas 05 y 06. Se leyó completo PROTOCOLO_COMUN y se revisaron sus dos prompts. Este corte examina una carga por producto con varios lotes y la entrada posterior existente.

## Inventario y fuentes

Fuentes precisas del tramo: 08:317–336 (INV-01a y 01b), 07:50 (RN-01) y 07:181 (RN-14), matriz03:83–91 y adendas de BUG-005/011/024/032/033, tareas16:111–120 y QA-FIX-INV-01, planificación14:77, backlog09:49/97, CONTROL_SPRINTS:15/63 y guía21. Diseño02 y alcance01 aportan el flujo de carga inicial. Los estados históricos de sprints describen entregas y se conservaron. El libro de planificación no está presente y su procedencia permanece inventariada en00.

| Elemento | Clasificación y comportamiento esperado | Resultado del corte |
|---|---|---|
| INV-01a/CA01, RN-01/29 | SELECCIONADO. ALMACENERO confirma una única carga por producto | Navegador, peticiones directas y carrera PostgreSQL. ADMIN y VENDEDOR reciben 403 por GET y POST. |
| INV-01a/CA02, RN-03 | SELECCIONADO. Número no vacío, normalizado y único por producto. Cantidad entera positiva, costo positivo de cuatro decimales y vencimiento futuro en Lima | Se ejercitaron duplicados normalizados, mismo número en productos distintos, fecha de hoy, cantidades y costos inválidos, máximos válidos y número largo. |
| INV-01a/CA03 | SELECCIONADO. Carga atómica y única, incluidos inválidos y reenvío | Comparación de instantáneas después de cancelar, rechazar y repetir. Dos cargas simultáneas produjeron un ganador y un rechazo. |
| INV-01a/CA04, RN-14 | SELECCIONADO. Suma de cantidades, disponibilidad y promedio ponderado | A recibió 12 a S/2 y 6 a S/5. Resultado 18 unidades y costo 3.0000. B y C recibieron 4 a S/1 y 2 a S/4, con seis unidades y costo 2.0000 cada uno. VENDEDOR consultó las fichas. |
| INV-01a/CA05, RN-19 | SELECCIONADO. Identidad del lote, ingreso inmutable y orden FEFO | PARCIAL. Se conservaron los campos de los lotes iniciales después de reposición y reenvíos. No se probó modificación directa del instante de ingreso ni el desempate FEFO completo. |
| INV-01b/CA01, RN-14 | IMPLEMENTADO ADICIONAL. Entrada posterior recalcula el costo | Dos unidades nuevas a S/6 dejaron A con20 y costo3.3000. Los lotes previos conservaron todos sus campos. |
| INV-01b/CA02 | SELECCIONADO EN CÓDIGO. Promedio de cuatro decimales mostrado con dos y costos históricos conservados | PARCIAL. Se comprobó 3.3000 en base y S/3,30 en pantalla. Este escenario no contiene ventas previas. La brecha de costo histórico documentada en03-Q sigue en11. |
| RN-01 frente a entrada directa | CONFLICTO DE FUENTES. RN exige solicitud aprobada. La pantalla existente confirma sin referencia de reposición | El ensayo documenta el comportamiento. La selección de proceso sigue pendiente. |
| SOL-01/02/03/04/05a/05b, 08:395–460 | PREVISTO/FUTURO en el tramo. Solicitud, lista, aprobación, rechazo, recepción total y parcial | Inventariados por ID. No se ejecutaron como proceso. |
| PROP-03-RET-T01 | PARCIAL. Recepción de mercancía de tres productos y varios lotes | Tres operaciones por producto. El lote de12 usa una cantidad de unidades contadas en el escenario. La conversión de embalaje y la recepción multiproducto indivisible siguen propuestas. |
| PROP-03-RET-T03/05/06/11 | Ejercicios acotados de duplicados, reenvío, concurrencia y roles | Evidencia secuencial y tres carreras. Desconexión con respuesta incierta y proveedor desactivado simultáneamente quedan pendientes. |

## Pantallas, campos y salidas

ALMACENERO accede desde el inicio a «Registrar existencias iniciales» y «Registrar entrada de mercadería». Las rutas son `/inventario/carga-inicial/`, `/inventario/entrada/` y la constancia `/inventario/cargas/<uuid>/`. El alias de constancia se conserva en inventario previo y no se ejercitó en este corte.

| Campo o acción | Tipo, valor inicial, límites y efecto |
|---|---|
| Producto | Selección requerida, inicialmente vacía. La lista incluye nombre y código. Alta inicial filtra activos con categoría activa y sin carga. Entrada posterior requiere carga previa. La elección asigna todos los lotes de ese envío a un producto. |
| Proveedor | Selección opcional, inicialmente «Sin proveedor asignado». La lista ofrece proveedores activos. El ensayo seleccionó un proveedor ficticio en las tres cargas y la reposición. |
| Número de lote | Texto requerido por fila utilizada, máximo64. Se recortan espacios exteriores y normaliza a mayúsculas. El mismo número se admite para productos distintos. |
| Cantidad | Entero requerido por fila, 1–999999. El escenario introduce unidades explícitas. La cantidad del paquete no se deduce del código. |
| Costo unitario | Decimal requerido, 0.0001–9999999.9999, hasta cuatro decimales. El formulario rechaza notación científica. |
| Vencimiento | Fecha requerida, futura respecto de Lima y hasta20 años según validación existente. Se probaron hoy, mañana y fechas futuras. La frontera exacta de20 años continúa pendiente. |
| Filas de lotes | Formset con una fila mínima y tres adicionales. Las filas vacías adicionales se omiten. Una fila inválida rechaza la operación completa. El formulario no ofrece añadir filas dinámicamente. |
| Confirmar existencias / Confirmar entrada | POST con producto, proveedor y filas. El servidor vuelve a validar y redirige a constancia al guardar. |
| Cancelar / Volver al inicio / Ver inventario | Navegación por GET. Cancelar antes de confirmar conservó la base comercial. |
| Constancia | Producto, responsable y fecha de carga inicial, saldo físico actual, costo promedio actual, tablas de lotes iniciales y posteriores. Proveedor, cantidad ingresada/disponible, costo, vencimiento y responsable de entrada quedan visibles. |
| Avisos | Vencimiento posterior a hoy, número repetido, lote ya existente, carga ya registrada o producto no disponible. Los rechazos HTTP y de formulario se cotejaron con persistencia. La reposición muestra mensaje de éxito. |

La constancia conserva el UUID de carga inicial como referencia técnica. Las entradas posteriores se distinguen mediante `is_initial=False` en sus lotes. La implementación actual carece de una cabecera comercial independiente por recepción posterior. Esa carencia debe considerarse al definir trazabilidad por envío y respuesta incierta.

## Hallazgos y correcciones

**H-03AB-01, prioridad alta, corregido.** La validación de servicio admitía cantidades fraccionarias, booleanos, cantidades superiores al límite del formulario y números de lote mayores de64. Un costo Decimal NaN provocaba una excepción de cálculo. Se reprodujo mediante llamadas a ambos servicios en base de prueba, combinando un lote válido y otro inválido. El formulario ya rechazaba estas entradas habituales. Se añadieron validaciones previas a las escrituras compartidas por carga inicial y entrada posterior. La prueba conserva costo, cabecera y lotes al rechazar. Los máximos válidos y costo mínimo mantienen su valor.

**H-03AB-02, prioridad media, corregido.** La ayuda de carga inicial limitaba verbalmente la función a enlatados, en conflicto con DOC03-01 aceptado. Ahora indica producto, cantidades en unidades y vencimiento.

**H-03AB-03, prioridad media, corregido.** La constancia afirmaba que todos los lotes se guardaron en una sola operación aunque mostraba reposiciones, y presentaba responsable y fecha iniciales sin identificarlos como tales. Los textos ahora describen la carga inicial y las entradas posteriores. El estado visible se refiere a carga inicial confirmada, evitando afirmar disponibilidad comercial a partir de la mera existencia de la carga.

**DOC-03AB-01, abierto.** RN-01 requiere solicitud aprobada para reposición. Alternativa A mantiene entrada directa como alcance seleccionado y requiere una revisión expresa de esa regla. Alternativa B implementa solicitud y aprobación, con recepción total/parcial, antes de considerar cumplida RN-01. La evidencia técnica de este corte no decide entre ambas.

## Reproducción y continuidad

```powershell
$python = 'r1-pmv/.venv/Scripts/python.exe'
$support = 'auditoria_por_etapas/resultados/soporte'
& $python -X utf8 "$support/audit03y_browser_run.py" ab-receipt
& $python -X utf8 "$support/audit03ab_pg.py"
$env:AUDIT03K_DEFAULT_COOKIES = '1'
& $python -X utf8 "$support/audit03k_run.py" tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

Cada corrida crea bases propias y marcadas. El PostgreSQL es un clúster privado nuevo. El soporte espera bloqueos reales con conexiones diferentes y mide ganador, rechazo y saldo. Los servicios se detienen y se cotejan hashes de bases protegidas al terminar.

**Cursor 05-B / INV-01a-CA02 y PROP-03-RET-T04/T06.** Formulario abierto con proveedor activo, desactivación desde otro rol, y confirmación de carga/entrada. Verificar revalidación de proveedor en servicio, simultaneidad en PostgreSQL, rechazo completo y mensaje. Completar vencimiento en las fronteras Lima y la conservación de fecha de ingreso antes de cerrar CA05. Recepción multiproducto en una operación, cuarentena, devoluciones y retiros permanecen en el traspaso de recepción y retiros.

## Evidencia final y conservación

[Chrome, 79 comprobaciones](../evidencias/03-AB-ab-receipt-20261111T170552228012Z-419c81d4/browser.json) · [Constancia revisada](../evidencias/03-AB-ab-receipt-20261111T170552228012Z-419c81d4/reposicion.png) · [PostgreSQL, tres carreras](../evidencias/03-AB-postgresql-20261111T170434574228Z.json) · [Regresión, 337 métodos](../evidencias/03-K-tests-20261111T170342686891Z/result.json).

Las 79 comprobaciones del navegador usan Chrome real con teclado automatizado. El ensayo representa una caja de12 mediante la cantidad explícita 12 en la fila del lote. La entrada del teléfono y la conversión automática de cajas no se ejercitaron. Los saldos finales fueron A20/B6/C6. Las tres carreras PostgreSQL observaron bloqueos con conexiones distintas y verificaron costo y saldo. El SHA256 de la base original y de las bases anteriores se conservó.

La prueba de límites de servicio recorre seis entradas inválidas en dos operaciones (12 subcasos) y un caso adicional de máximos/mínimos válidos. Los primeros dos intentos de esta prueba fallaron al preparar el nombre del usuario y el código ficticio, antes de evaluar la recepción. Se corrigió ese soporte. La siguiente corrida reprodujo ocho aceptaciones indebidas y dos errores NaN. La regresión final aprobó ambos métodos nuevos junto a los335 anteriores. [Preparación inicial](../evidencias/03-K-tests-20261111T170225624727Z/tests.txt) · [Segunda preparación](../evidencias/03-K-tests-20261111T170257775466Z/tests.txt) · [Defecto reproducido](../evidencias/03-K-tests-20261111T170315564731Z/tests.txt).
