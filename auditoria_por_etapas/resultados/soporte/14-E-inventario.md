# Inventario de costo y diagnóstico de legado 14-E

Primera pasada, continuación de 14-D, 13/11/2026 Lima. Cursor de entrada 14-E-KARDEX-01. El sublote profundiza la dependencia de valoración DOC-03AH-01 antes de completar las asignaciones y el Kardex en 14-F. La base funcional inventariada es 08 SHA256 `e8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847`. El build y los resultados de ejecución de 14-E se registran en su informe y manifiestos. Esta sección documenta lectura de fuentes y diseño, con estado inicial previo a las correcciones.

Se consultaron el protocolo y la continuidad, 08 DOC-03AH/AI, DEC-11-MODELO, DEC-08-KARDEX, RN-14/28 y HUs pertinentes, diseño02, tareas16 y la evidencia14-D. Los datos operativos existentes no fueron leídos. La inspección de legado usa estructuras y migraciones como evidencia, y prescribe comprobaciones sobre un clon explícito cuando exista autorización para examinar sus datos. [Informe vigente](../ETAPA-14.md) · [Inventario14-D](14-D-inventario.md) · [08](../../../08_Historias_de_Usuario.md) · [02](../../../02_Diseno_Tecnico_R1_PMV.md) · [16](../../../16_Task_Breakdown.md).

## Selección y denominadores

Las tres HU principales son INV-01b, INV-02 y VEN-01c, con 12 CA base inventariados. El foco funcional es el costo al recibir, vender y dar de baja. Los criterios de INV-03 se consultan como dependencia del mismo algoritmo y de sus efectos sobre conteos físicos. Completar la fórmula y capturar costo de salida verifica condiciones parciales de estas HU, mientras referencia propia de recepción, constancia dedicada y asignaciones permanecen en sus encargos.

| HU y CA | Necesidad y tramo seleccionado | Clasificación inicial y límites | Antecedente |
|---|---|---|---|
| HU-INV-01b/CA-01 | ALMACENERO recibe10 a6 después de físico18 promedio3. El costo usa las28 unidades físicas | INCUMPLE por excluir vencidos del Q anterior. Identidad propia/idempotencia de recepción pertenecen a DOC-03AI y continúan pendientes | [06](../ETAPA-06.md) |
| HU-INV-01b/CA-02 | Almacenero y ADMIN contrastan promedio guardado4.0714 y mostrado4.07 | NO EJECUTADO nuevo. Debe conservar costos de ventas anteriores | [06](../ETAPA-06.md) |
| HU-INV-02/CA-01 | Baja de lote por cantidad válida, conservando costo de salida | Cantidad/causa tienen muestras14-D. Costo nuevo NO EJECUTADO y sin snapshot en modelo inicial | [08](../ETAPA-08.md) · [14-D](../ETAPA-14.md#vigente-14-d) |
| HU-INV-02/CA-02 | Vencido admite caducidad o robo explicado, rechaza daño | HEREDADO de14-D para causa. Revalidar costo con una baja vigente y otra vencida. La expiración no cambia valor por sí sola | [Variantes14-D](../evidencias/14-D-20261113/servidor/variantes-despues.json) |
| HU-INV-02/CA-03 | Detalle daño/robo y autor responsable | HEREDADO de14-D. Revalidar que el nuevo costo se guarda con la misma baja y actor | [14-D](../ETAPA-14.md#vigente-14-d) |
| HU-INV-02/CA-04 | Constancia correlativa de baja | PARCIAL heredado. Agregar snapshot de costo no implementa consulta dedicada inmutable |
| HU-VEN-01c/CA-01 | Error de cobro no deja venta/costo/saldo/correlativo parcial | Revalidación requerida tras modificar salida/costo. Fronteras monetarias completas conservan evidencia previa | [11](../ETAPA-11.md) |
| HU-VEN-01c/CA-02 | Efectivo/vuelto y total de caja | Revalidación de conexión. La valoración interna no modifica precio, total, IGV o vuelto | [11](../ETAPA-11.md) |
| HU-VEN-01c/CA-03 | FEFO consume solo vigentes y nunca stock negativo | Verificar venta1, físico27 promedio4.0714. Caso con vencido remanente mantiene promedio aunque vigente se agote | [11](../ETAPA-11.md) · [14-D](../ETAPA-14.md#vigente-14-d) |
| HU-VEN-01c/CA-04 | Commit de venta/detalles/costo/stock y rechazo integral | PARCIAL heredado por asignaciones faltantes. 14-E exige atomicidad de los campos nuevos o afectados |
| HU-VEN-01c/CA-05 | Reenvío conserva una salida y un costo | Revalidar reintento sin segunda actualización de promedio. Carreras reales exigen etapa15 |
| HU-VEN-01c/CA-06 | SaleLine conserva fotografía de costo4.0714 | Campo existente, requiere contrastar captura antes de poner promedio0 al agotar físico. NULL histórico se mantiene desconocido | [11](../ETAPA-11.md) · [12](../ETAPA-12.md) |

Hay 4 criterios complementarios DOC-03AH-01/C-01..04 seleccionados para contraste. C-04 conserva concurrencia PostgreSQL y caída de proceso fuera de la evidencia SQLite. Los 4 criterios DOC-03AI, los 4 de DEC-11-MODELO y los 3 de DEC-08-KARDEX son 11 criterios de dependencia inventariados para 14-F, cuya totalidad sigue pendiente. RN-14/28 fijan valoración/costo histórico, y RN-03/19/25/29/30 se revalidan solo en las conexiones afectadas.

| Contrato y tarea16 | Regla verificable | Evidencia exigida a este sublote |
|---|---|---|
| DOC-03AH-01/C-01, RN-14 | Entrada pondera Q físico anterior y promedio bloqueado, incluyendo vencidos | Fixture18@3, vencido8/vigente10, entrada10@6 → físico28, vigente20, costo4.0714 |
| DOC-03AH-01/C-02, RN-14/28 | Salida conserva promedio si Q>0, captura costo antes de retirar, Q=0 deja promedio0 | Venta, baja y ajuste negativo con costos de lote diferentes. Agotamiento físico, agotamiento solo vendible y relectura de snapshot |
| DOC-03AH-01/C-03, HU-INV-03 | Ajuste positivo con Q>0 valora al promedio vigente. Q=0 exige costo documentado | +2 conserva4.0714 y registra costo de ajuste. Q=0 sin costo fiable rechaza con huella estable |
| DOC-03AH-01/C-04, CT-ROLLBACK | Rechazo y rollback no dejan costo ni saldo parcial | Fallo inducido después de escritura y comparación de tablas. PG y muerte de proceso mantienen pruebas propias |
| DOC-03AI-01/C-01..04 | Recepción propia, referencia R, reintento, contenido/autor/origen | Pendiente14-F. La FK actual de lotes a carga inicial carece de identidad de recepción propia |
| DEC-11-MODELO/C-01..04 | Asignación lote, snapshots y desconocido histórico | Pendiente14-F. SaleLine.unit_cost existente permite costo de venta14-E, sin atribuir lotes no persistidos |
| DEC-08-KARDEX/C-01..03 | Saldo real, origen por lote, filtros y paginación | Pendiente14-F, después de costos y asignaciones. Una nueva columna costo no completa estos criterios |
| RN-05/C-02..04 | Ajuste de lote nuevo, constancia y reintento/carrera | Continúan pendientes según inventario14-D. El ajuste Q=0 sin costo se rechaza hasta disponer de entrada fiable |

## Diagnóstico inicial verificable por código

| ID | Observación inicial | Efecto inferido que la prueba debe reproducir | Prioridad |
|---|---|---|---|
| E14-COSTO-01 | register_stock_entry calcula previous_quantity con expiration_date>fecha | Q10@3 +10@6 produce4.5000 aunque hay18 físicos. Esperado4.0714 | Alta |
| E14-COSTO-02 | _recalculate_product_average_cost repondera lotes vigentes remanentes y solo recurre a vencidos si no quedan vigentes | Baja/ajuste modifica costo por cambiar mezcla de lotes y la fecha altera el universo de cálculo | Alta |
| E14-COSTO-03 | Recalculador actual solo escribe si total_qty>0 | Última baja/ajuste puede dejar costo positivo con físico0 | Alta |
| E14-COSTO-04 | checkout captura SaleLine.unit_cost y descuenta lotes, sin normalizar promedio al agotar físico | Última venta deja promedio positivo aunque Q=0. Poner0 antes de crear SaleLine perdería costo de la venta | Alta |
| E14-COSTO-05 | StockWriteOff y PhysicalAdjustment iniciales no contienen costo | El historial de salida no puede demostrar costo vigente al ocurrir la merma o ajuste | Alta |
| E14-COSTO-06 | Ajuste positivo aumenta Lot.initial_quantity para respetar available<=initial | Ese campo funciona como capacidad mutable. Vistas reconstruyen cantidad original restando ajustes positivos. Debe conservarse coherencia de recepción y no presentarse capacidad como ingreso original | Media |
| E14-COSTO-07 | Tests bug005 exigen excluir vencidos o reponderar remanentes | El resultado verde de esas aserciones consagra política histórica incompatible con08. Reescribir expectativas requiere conservar reproducción anterior y contrato que justifica el cambio | Alta |
| E14-COSTO-08 | Product.average_cost es no nullable y permite0, sin estado/origen de valoración | Q>0/C=0 o positivo de algoritmo antiguo no acredita valoración fiable. El valor por sí solo no distingue desconocido de conocido | Alta |

Fuentes del estado inicial. [Inventory services](../../../r1-pmv/inventory/services.py) · [Inventory models](../../../r1-pmv/inventory/models.py) · [Sales services](../../../r1-pmv/sales/services.py) · [Sales models](../../../r1-pmv/sales/models.py) · [Pruebas históricas de inventario](../../../r1-pmv/inventory/tests.py).

## Rutas, campos, mensajes y salidas afectadas

El inventario contiene 9 patrones de ruta directamente conectados y 15 filas de campo/salida. Formularios y consultas heredan el detalle previo de14-D. Las ramas nuevas se deben registrar en capturas de14-E con literal, rol, estado, valor y testigo de persistencia.

| Ruta | Rol y acción | Contraste nuevo y literal/salida inicial |
|---|---|---|
| /inventario/entrada/ | ALMACENERO GET/POST | «Entrada de mercadería», selección de producto con carga previa, lotes/costo/fecha. Mensaje «Entrada de lotes registrada para «{producto}». Costo promedio actualizado.» requiere commit con promedio correcto |
| /inventario/cargas/{id}/ | ADMIN/ALMACENERO GET | «Costo promedio» mostrado con2decimales, «Existencias físicas», lotes/entrada/autor. Es consulta de carga compartida, origen propio aún pendiente |
| /inventario/stock/ | ADMIN/ALMACENERO GET | «Stock físico», «Stock vigente», estado y alertas. El costo no transforma unidades vencidas en vendibles |
| /inventario/bajas/nueva/ | ADMIN/ALMACENERO GET/POST | «Cantidad a dar de baja», «Motivo», «Detalle (obligatorio para Daño y Robo)», «Baja {correlativo} registrada correctamente.» |
| /inventario/ajustes/nuevo/ | ADMIN GET/POST | «Ajuste (positivo=entrada, negativo=faltante)», «Motivo del ajuste», «Confirmar ajuste», «Ajuste físico registrado correctamente.». Rechazo Q0 requiere mensaje preciso y sin escritura |
| /ventas/cobrar/ | VENDEDOR propio GET/POST | «Efectivo recibido (S/)», «Confirmar cobro», precio completo. Costo promedio lo decide servidor bloqueado, nunca un campo del POS |
| /ventas/constancia/{id}/ | ADMIN o VENDEDOR propio GET | Fotografía de importes y aviso interno. El costo histórico sigue fuera de la constancia cliente |
| /inventario/productos/{id}/movimientos/ | ADMIN/ALMACENERO GET | «Fecha», «Tipo», «Detalle», «Cantidad», «Responsable» y stock actual. Si se añade costo interno, diferencia conocido/desconocido sin derivarlo de lotes actuales |
| /ventas/historial/ | ADMIN global o VENDEDOR propio GET | Total/efectivo/vuelto de la misma venta. Valoración conserva precio/caja/historia |

| Campo o salida | Tipo, inicial y límite | Propósito y persistencia | Requisito o pendiente |
|---|---|---|---|
| product en recepción | UUID requerido, selección vacía, activo/categoría activa y carga previa | Releer y bloquear Product antes de Q/C y lotes | INV-01b, RN-29 |
| supplier en recepción | UUID activo opcional, «Sin proveedor asignado» | Conservar proveedor en lotes. No prueba referencia propia de recepción | DOC-03AB/AI |
| lots-number | Texto1..64, vacío requerido, normalización ya inventariada | Identidad comercial y unicidad actual | DEC-05, origen propio pendiente |
| lots-quantity | Entero1..999999, vacío requerido, ASCII | q recibido, suma exacta sin float | INV-01a/b |
| lots-unit_cost | Decimal4 positivo0.0001..9999999.9999, sin exponentes | Costo de adquisición de la entrada, no cambia el costo histórico de salidas | RN-14 |
| lots-expiration_date | Fecha ISO >hoy Lima, máximo20años | Vendibilidad de nuevo lote. Fecha sola no cambia C | RN-03/14 |
| Product.average_cost | Decimal(14,4), inicial0 para producto sin existencias | Costo vigente bloqueado. Q>0 conserva promedio en salidas. Q0 termina en0 | DOC-03AH |
| Baja quantity/reason/notes | Entero1..999999<=saldo, catálogo3causas, detalle obligatorio daño/robo | Una fila y salida con causa real, costo y actor | INV-02, RN-05 |
| Ajuste delta | Entero no cero −999999..999999, <=saldo si negativo | Delta físico. Positivo Q>0 usa promedio. Q0 sin costo fiable rechaza | INV-03, DOC-03AH/C-03 |
| Ajuste reason | Texto1..300 recortado, sin NUL, vacío inválido | Procedencia del conteo. Motivo libre por sí solo no acredita valor monetario desconocido | INV-03 |
| StockWriteOff.unit_cost propuesto | Decimal(14,4), nullable para legado, sin default0 | Capturar C previo bloqueado por cada baja nueva. Historias anteriores conservan NULL | DOC-03AH/C-02 |
| PhysicalAdjustment.unit_cost propuesto | Decimal(14,4), nullable para legado, sin default0 | Costo aplicado al delta. Signo permanece en delta. Q>0 usa C previo | DOC-03AH/C-02/03 |
| SaleLine.unit_cost existente | Decimal(14,4), nullable para legado | Guardar C bloqueado antes de la salida. No actualizar al cambiar promedio posterior | RN-28, VEN01c/CA-06 |
| «Costo promedio» de carga | Salida2decimales, redondeo HALF_UP | 4.0714 guardado →4.07 mostrado. Nunca confundir redondeo de vista con costo persistido | INV-01b/CA-02 |
| Costo histórico en consulta interna |4decimales para revisión precisa, o salida marcada desconocida siNULL | ADMIN/ALMACENERO verifican; POS/constancia cliente conservan ausencia de costo | DEC-12-PERMISOS, RN-28 |

La entrada de costo para ajuste Q0 no existe en el formulario inicial. El sublote autoriza el rechazo íntegro cuando falta esa evidencia. Habilitar un formulario de ajuste inicial con costo/fuente y lote nuevo requiere completar las entradas y pruebas de INV-03 y RN-05/C-02 en su propio alcance. No se obtiene costo fiable de Lot.unit_cost por inferencia sobre la última compra.

## Mínimo técnico de migración y cálculo

Las garantías de valoración y costo de salida están aceptadas en RN-14/28 y DOC-03AH. La elección de dos campos nullable reutiliza el modelo actual, y fue seleccionada para este sublote por la coordinación de14-E. El cambio es aditivo, sin transformación de importes históricos. Sus resultados de migración y compatibilidad deben ser comprobados sobre una base temporal con filas anteriores.

1. Añadir unit_cost a StockWriteOff y PhysicalAdjustment con Decimal(14,4), null=True y editable=False. Mantener NULL de todas las filas antiguas, sin default0 ni actualización desde Product/Lot. Un CHECK puede impedir valores negativos permitiendo NULL. La obligatoriedad para nuevas operaciones vive en servicio autorizado y pruebas, dado el legado permitido.
2. Bajo el lock de Product, obtener Q físico previo y C vigente con precisión Decimal4. Recepción pondera usando todos los saldos físicos. Venta/baja/ajuste negativo captura C antes de la primera salida y lo mantiene mientras quede físico. Al llegar aQ0, actualiza únicamente el promedio vigente a0.
3. Ajuste positivo con Q>0 conservaC y su snapshot. Si Q0 y el caso de uso carece de costo documentado, rechaza antes de crear ajuste o mutar lote. No usa costo de compra antiguo para rellenar ese vacío.
4. Mantener las mismas transacciones, autorización e idempotencia de cada entrada normal. El fallo al crear snapshot, lote, baja o línea de venta revierte todas las mutaciones del intento. La identificación histórica de reintento ocurre antes de una política que pudiera reinterpretar el resultado anterior.
5. Mostrar NULL como dato no disponible cuando una consulta interna incluya costo. La evidencia de un snapshot nuevo no prueba que el costo base legacy usado fuera correcto. Se conserva la procedencia del corte de valoración.

La reversión de aplicación puede conservar columnas adicionales. Una migración inversa que quite columnas después de registrar costos destruiría esa evidencia, por lo que el ensayo debe diferenciar reversión de código de destrucción de datos. La compatibilidad de una aplicación antigua que vuelva a crear filas sin costo tiene que registrarse en el plan de recuperación y en la auditoría posterior. Ninguna migración operativa se ha ejecutado en esta revisión.

## Legado y diagnóstico read-only

Las migraciones permiten establecer las siguientes limitaciones sin abrir una base del usuario.

| Evidencia de esquema | Hecho comprobado | Consecuencia de diagnóstico |
|---|---|---|
| inventory.0004_lot_is_initial | Añadió is_initial con default=True | El valorTrue en lote migrado no demuestra por sí solo que perteneciera a la primera carga |
| inventory.0005_lot_responsible | Añadió responsable nullable | NULL significa ausencia de dato. Usar responsable actual de la carga como autor de otra recepción puede ser falso |
| sales.0004_saleline_product | Añadió FK producto nullable | Código histórico y código actual coincidentes no bastan para asignar identidad de producto inequívoca |
| sales.0005_saleline_unit_cost | Añadió costo nullable sin backfill | NULL histórico no admite sustitución automática por promedio de hoy |
| Lot.initial_quantity y ajustes positivos | La capacidad crece con cada ajuste positivo | La cantidad original se puede derivar solo cuando se acredita integridad del historial de ajustes del lote |
| StockWriteOff/PhysicalAdjustment anteriores | Carecen de fotografía de costo | Un cálculo retrospectivo requiere secuencia completa de entradas/salidas/costos y política aplicada. La fila actual no aporta todo eso |
| SaleLine sin asignaciones | Solo conserva producto, cantidad, precio/costo y venta | FEFO sobre el estado actual no identifica el lote realmente consumido en una venta antigua |

[Migraciones inventory](../../../r1-pmv/inventory/migrations) · [Migraciones sales](../../../r1-pmv/sales/migrations).

El comando recomendado debe recibir una ruta explícita de clon SQLite y abrirla mediante URI `mode=ro`, o una conexión PostgreSQL a clon con transacción `READ ONLY`. Debe rechazar invocaciones sin destino explícito y conservar motor, fecha Lima del corte, migraciones, hash/tamaño del clon y fecha de ejecución en un informe sanitizado. El comando no debe ejecutar migrate, seed, update o recalcular, ni deducir conexión operativa de .env. El diseño del comando se documenta aquí y su ejecución no está acreditada por este inventario.

| Consulta read-only propuesta | Resultado requerido | Decisión posible |
|---|---|---|
| Por Product, SUM(Lot.available_quantity), suma de vigentes y average_cost | Q físico/vigente/C, incluyendo productos sin lotes | Q0/C>0 revela costo residual. Q>0/C<=0 necesita investigar valoración. Un C positivo tampoco acredita política correcta |
| Conteos de SaleLine.unit_cost IS NULL y =0, con product NULL | Cobertura histórica por cantidad de líneas y unidades. IDs de muestra sanitizados | Conservar NULL/desconocido. Investigar ceros sin convertirlos por defecto |
| Conteos de nuevas columnas costo en bajas/ajustes por periodo/corte | Filas NULL antiguas frente a operaciones que deberían capturar snapshot | Distinguir legado de omisión posterior al cambio, sin afirmar que fecha por sí sola acredita versión desplegada |
| Lotes de producto, número normalizado, vencimiento, initial/available y suma ajustes positivos | Disponible>=0, original reconstruible y límites de capacidad | No corregir inconsistencias silenciosamente. Identificar datos que impiden reconstrucción |
| Filas is_initial, responsible NULL y FK carga | Cobertura de origen y autor, contradicciones de referencia | Mantener origen desconocido cuando falta prueba. El default de migración impide concluir inicial por flag aislado |
| SaleLine.quantity frente a SUM(asignación.quantity), cuando exista tabla14-F | Completo, ausente o parcial por línea, referencias de producto/lote concordantes | Rechazar nueva incoherencia. Legado ausente permanece sin atribución de lote |
| Conteos de venta/baja/ajuste/carga y sumas de cantidades por producto | Conciliación de saldos y pérdidas de historia | Saldo actual coincidente es evidencia de balance, no prueba de costo exacto ni origen |

Ejemplo de consulta parametrizada de diagnóstico físico en SQLite, para una conexión al clon ya abierta en modo lectura. `:hoy_lima` se obtiene del reloj de negocio declarado. La consulta identifica candidatos y no establece una corrección.

```sql
SELECT p.id,
       COALESCE(SUM(l.available_quantity), 0) AS physical_quantity,
       COALESCE(SUM(CASE WHEN l.expiration_date > :hoy_lima
                         THEN l.available_quantity ELSE 0 END), 0) AS current_quantity,
       p.average_cost
FROM catalog_product AS p
LEFT JOIN inventory_lot AS l ON l.product_id = p.id
GROUP BY p.id, p.average_cost
ORDER BY p.id;
```

El despliegue sobre datos existentes requiere clasificar el estado por producto. Una base vacía o una fixture con costo acreditado permite aplicar la fórmula aceptada inmediatamente dentro del entorno autorizado. Una base con historia completa puede sustentar una apertura de valoración documentada. Si la historia es insuficiente, DOC-03AH exige un corte de valoración explícito y autorizado antes de modificar valores operativos. Las alternativas son conservar consulta histórica con cobertura desconocida mientras se investiga, o registrar una apertura sustentada por conteo/costo y fuente. Ninguna alternativa requiere paralizar las correcciones y pruebas en bases nuevas aisladas.

El costo fiscal, la relación de adquisición con IGV y la rentabilidad real requieren datos del negocio y la etapa normativa. La política de promedio interno de08 ya está aceptada y basta para la corrección técnica acotada. No hay fundamento para convertir esa investigación fiscal en requisito previo de las pruebas ficticias de14-E.

## Dependencias de 14-F y diseño propuesto de asignaciones

La siguiente solución es una recomendación mínima para satisfacer garantías aceptadas, pendiente de implementación/selección concreta en14-F.

| Elemento | Propuesta mínima | Integridad y legado |
|---|---|---|
| Asignación real de venta | SaleLotAllocation con FK SaleLine y Lot, cantidad entera positiva, unicidad por línea/lote y FK PROTECT | Crear exactamente durante el bucle FEFO, en la misma transacción. Suma por línea=cantidadvendida y producto de lote=producto de línea. Esas igualdades requieren validación transaccional, no un CHECK trivial entre filas |
| Migración de asignaciones | Crear tabla vacía y poblar solo nuevas ventas de código actualizado | Cero asignaciones de una venta anterior indica cobertura ausente. No ejecutar FEFO retrospectivo ni adjudicar stock actual a venta pasada |
| Cantidad parcial | Comprobar suma para toda línea nueva y diagnosticar faltantes | Marcar parcial/desconocido en consultas internas si faltan filas. No presentar detalle incompleto como cobertura total |
| Fotografía del lote | Evaluar snapshot de número/vencimiento si el maestro admite cambios que afecten historia | Una FK protege identidad y existencia, pero no la inmutabilidad del contenido. La solución debe acreditar lectura histórica coherente |
| Caja/vendedor/posición | Snapshots nombre vendedor/código caja y posición de línea aceptados por DEC-11-MODELO | Nuevos valores se fijan al confirmar. El legado no puede reconstruir nombres pasados a partir del maestro actual |
| Recepción propia | Entidad simple con UUID/referenciaR/actor/instante/clave/huella y vínculo de lote | DOC-03AI completo. No agrupar lotes legacy por timestamp aproximado como prueba de una recepción |
| Kardex | Movimientos desde orígenes durables con orden total, saldo real, filtros y25porpágina | La consulta de periodo calcula apertura desde historia conocida/corte autorizado. Filtrar tipos no borra el efecto de movimientos excluidos en el saldo real |

## Recomendaciones y aceptación

| Encargo | Beneficio | Riesgo y alternativa | Costo relativo e impacto |
|---|---|---|---|
| DOC-03AH, cálculo y captura de costo | Mantiene valoración consistente entre almacenero, vendedor y ADMIN | Usar lotes remanentes modifica valor tras salidas. Alternativa de conservar algoritmo previo incumple el contrato ya aceptado | Medio. Servicios inventory/sales, migración aditiva, regresión de recepción/baja/ajuste/cobro |
| Diagnóstico read-only y corte de valoración | Evita atribuir certeza a costos legacy contaminados | Un backfill desde costo actual altera historia. Clasificar desconocido y apertura documentada preserva procedencia | Bajo/medio diagnóstico, medio en regularización. Requiere datos reales antes de una intervención operativa |
| NULL en snapshots antiguos | Identifica cobertura de forma verificable | Default0 produciría apariencia de costo gratuito conocido. Mostrar «No disponible» mantiene significado | Bajo. Modelos, consultas y pruebas de legado |
| Asignaciones de lote14-F | Permite reconstruir venta real y conciliar stock | Reaplicar FEFO a posteriori puede escoger otros lotes. Tabla nueva por salida evita inferencia | Medio. Migración, cobro, rollback, consulta y legado |
| Recepción/Kardex14-F | ADMIN puede seguir cantidad, origen y saldo real por operación | Un Kardex basado en fechas/flags incompletos puede inventar origen y saldo | Medio/alto. DOC-03AI, DEC-08 y diagnóstico histórico previos |
| Revalidación PG de locks/atomicidad | Evita promedios y saldos mezclados bajo competencia real | SQLite no reproduce select_for_update. Mantener alcance secuencial explícito permite avanzar evidencia local | Medio. Conexiones/barreras/rollback en etapa15, con casos concretos de14-E |

El fundamento de aceptación funcional proviene de RN-14/28 y DOC-03AH ya vigentes. El encargo de continuación14-E selecciona cálculo, snapshots de costo y rechazo de ajuste sin costo fiable. Los componentes de14-F y la herramienta de diagnóstico permanecen propuestas de implementación sobre requisitos existentes, con sus alternativas registradas. El informe de ejecución debe conservar las pruebas antes/después, la migración ensayada y los límites de legado.

Cursor de este inventario, contrastar F-COSTO contra reproducción inicial y final14-E, verificar que unit_cost de baja/ajuste queda4.0714 y promedio0 solo tras agotamiento físico total. Después continuar14-F con asignaciones reales y consulta histórica de desconocidos antes de saldo/filtros de Kardex. La evidencia heredada14-D conserva su build y no aprueba automáticamente los criterios modificados.

## Propuestas exactas para conciliar la planificación

Las siguientes actualizaciones documentales deben acompañar el resultado real14-E. Son propuestas de redacción y estado. La evidencia final de pruebas/migración/navegador determina qué se puede marcar ejecutado. Los contratos normativos de fórmula, origen y costo permanecen íntegros.

| Archivo y ubicación | Cambio propuesto | Fundamento |
|---|---|---|
| 08, RN-14, última frase de estado «implementación pendiente» | Sustituir por «14-E implementa el promedio de entrada sobre existencia física y conserva el promedio en salidas, con puesta a cero al agotarse el físico. Baja y ajuste capturan el costo aplicado en campos históricos nullable para legado. La cobertura de ejecución y los pendientes de costo documentado Q0, legado, concurrencia y recuperación constan en ETAPA-14.» | Registrar implementación acotada sin cambiar política o certificar criterio completo |
| 08, CP-DOC-03AH-01-001, Estado/Evidencia | Registrar «EJECUTADO PARCIAL en primera pasada14-E» solamente cuando existan resultados. Especificar casos ejecutados, base y build. Mantener C-04 parcial respecto de PG y caída real. Mantener ajusteQ0 con costo documentado pendiente si solo se entrega rechazo sin costo | Diferenciar implementación de fórmula, validación de rechazo y totalidad del caso |
| 08, DOC-03AH, apartado Datos | Añadir «Los costos de bajas y ajustes anteriores a la captura permanecenNULL cuando no se dispone de evidencia. Las nuevas salidas registran el promedio previo bloqueado. El valor vigente se puede poner a0 por agotamiento sin modificar esos costos históricos.» | Completar representación adoptada sobre regla aceptada, evitando backfill y valor0 ficticio |
| 08, CP-INTEGRACION-ROLES-001 | Mantener intacto resultado14-D. Añadir referencia al nuevo contraste F-COSTO en14-E como dependencia revalidada, identificando build propio | Conservar evidencia anterior y separar secuencia con costos distintos |
| 02, §2.5 Dinero/costo | Añadir que entrada usa Q físico previo bajo lock, helper de salida conservaC o deja0 siQfinal0, y snapshots WriteOff/Adjustment se fijan antes de salida. SaleLine.unit_cost ya existente conserva el mismo contrato | Documentar mecanismo coherente y orden que evita capturar0 en última salida |
| 02, §2.9 Legado/migración | Registrar migración aditiva nullable sin default/backfill, comparación de datos anteriores, diagnóstico sobre clon explícito read-only y necesidad de corte autorizado antes de regularizar costo operativo incierto | Separar campos históricos desconocidos de una apertura de valoración |
| 02, §2.3 Modelo | Mantener asignaciones, snapshots vendedor/caja y origen propio como brechas14-F. La nueva captura de costo en baja/ajuste no sustituye esas garantías | Evitar cierre de arquitectura por una parte del modelo |
| 16, fila DOC-03AH-01 | Estado parcial con cálculo/retirada/costo capturado implementados y evidencia14-E. Restantes, tratamiento operativo de legado, captura documentadaQ0, concurrenciaPG y caída postwrite | Mantener dependencias y preparación14-F |
| 16, fila RN-05 | Añadir costo de baja/ajuste nuevo capturado y revalidado según muestra. Mantener ajuste de lote nuevo, constancia dedicada y carreras | Distinguir costo de salida de constancia y origen |
| 16, DEC-11-MODELO y DEC-08-KARDEX | Mantener pendiente14-F, anotar dependencia DOC-03AH parcialmente resuelta y casos de asignación/desconocido/saldo que siguen | Cursor14-F con requisito trazable |

Después de actualizar08 corresponde regenerar07/09/03 y el índice derivado, conservar huella anterior y registrar huella final. Los cambios de estado de02/16 deben corresponder a los casos ejecutados. Una propuesta de diagnóstico read-only no acredita un diagnóstico de datos operativos ni una migración sobre esa base.

## Contraste final de este inventario · 13/11/2026

Las tablas iniciales anteriores describen el diagnóstico antes de corregir. El corte final implementó la fórmula sobre físico y la conservación del promedio, el reset a0 por agotamiento, los dos campos nullable de costo y el rechazo de ajuste+Q0 sin costo fiable. Migración0007 comprobada en base ficticia: campos previos intactos y costos nuevosNULL. Se revisó el orden transaccional de captura antes de salida y su uso desde venta/baja/ajuste.

[Resultados y clasificación de cada criterio](../ETAPA-14.md#vigente-14-e) · [Matriz de16 criterios](../evidencias/14-E-20261113/criterios-final.json) · [Decisiones aceptadas y pendientes](14-E-disposiciones.md). Los23/23 casos servidor,23 checkpoints Chrome y566/566regresión tienen ámbitos solapados. La revisión de código apoya el diseño; la evidencia de ejecución procede de esos artefactos. No se abrió una base operativa.

Las recomendaciones de diagnóstico y14-F siguen propuestas técnicas sobre necesidades ya existentes. El costo documentadoQ0, origen propio, asignaciones durables, consulta de costos desconocidos, constancia de merma y concurrencia/caída conservan los límites del informe. El cursor vigente es14-F-ASIGNACIONES-01, no una repetición del F-COSTO ya completado.
