# Disposiciones 14-H1 · 13/11/2026 Lima

Primera pasada, dependencia de `14-H-KARDEX-SALDOS-01`. El sublote se divide antes de presentar un saldo calculado: H1 captura el origen de cargas nuevas; H2 ejecutará saldo, filtros y paginación. Esta división conserva los criterios del Kardex y no los da por cumplidos.

El fundamento de aceptación es DOC-03AI-01 (cargas/entradas conservan autor, proveedor y cantidad original), DB-C07 del diseño y HU-INV-01a/04, dentro del encargo y la delegación técnica de integración ya aplicados en14-D/G. El protocolo, esta propuesta y el último «continúa» no amplían esa autorización. No cambia selección comercial, roles ni datos operativos.

| ID | Decisión, beneficio y alternativa | Riesgo, costo e impacto | Estado |
|---|---|---|---|
| D14H-01 |Capturar cabecera de carga y `InitialLoadLine` tipada. Permite distinguir cantidad original de capacidad mutable. Se reutiliza el patrón relacional de14-G; se descarta JSON sin esquema y no se añade libro genérico de eventos|Costo medio; migración aditiva y cuatro puntos de escritura. Una sola transacción protege cabecera/lotes/líneas/promedio|Aceptada por requisito existente, implementada y verificada en muestra H1|
| D14H-02 |Conservar NULL y cero líneas para legado. Mostrar cantidad original no disponible y datos actuales claramente rotulados|Menos historia cuantificable hasta obtener evidencia real. No inferir por FK, fecha, `is_initial` o resta de ajustes|Implementada y verificada; regularización operativa pendiente|
| D14H-03 |Separar nombre/código/autor/proveedor/RUC/costo originales de stock y promedio actuales; costo de lote a4, promedio a2|Costo bajo de UI; evita confundir el costo adquirido con promedio y estado actuales. Mantiene navegación y tabla desplazable|Concreción de presentación aceptada en08; Chrome y servidor|
| D14H-04 |Kardex enlaza la carga capturada y usa su cantidad/autor/proveedor. Entradas heredadas muestran cantidad no disponible|Costo bajo; el historial aún es descendente y carece de saldos/filtros/paginación. No atribuir esa brecha a legado solamente|Mejora acotada deINV04/CA03; H2 pendiente|
| D14H-05 |Actualizar dos expectativas de tests anteriores: costo original4 y contexto de lotes sin fotografía; ausencia de proveedor explícita|Las versiones anteriores están archivadas. No se quita cobertura de promedio2, roles, rollback, carga única o recepción independiente|Corresponde al contrato nuevo; no rebaja criterios para obtener verde|

La revisión visual aplica UI/UX Pro Max a datos ausentes y tablas móviles: explicar la ausencia, mantener una tabla desplazable con etiqueta y foco, evitar desbordar la página. No se crea un sistema visual nuevo. La consulta a la guía devolvió Table Handling y Empty States; ambas son pertinentes. Las capturas finales y las huellas de persistencia sustentan la aplicación.

## Recomendaciones que permanecen abiertas

| Necesidad | Beneficio | Riesgo/costo/impacto y alternativas | Estado |
|---|---|---|---|
| Saldo por lote y total, filtros por período/tipo y páginas25 |Conciliar operaciones con existencias|Costo medio; recomputar todo antes de filtrar/paginar y rechazar reconstrucción incierta. Alternativa de saldo inicial de corte requiere procedencia y autorización de datos|Aceptada enINV04/DEC08; cursor H2, no implementada enH1|
| Diagnóstico de legado en clon autorizado |Determinar qué origen puede acreditarse|Costo medio; solicitar documentos reales y registrar procedencia. No fabricar fotografías desde valores actuales|Investigación, hechos de negocio pendientes|
| Protección histórica ante escritura directa y consistencia entre FK |Evitar alteración fuera de servicios|Costo medio; evaluar restricciones/privilegios o triggers según motor. La migración H1 no asegura inmutabilidad SQL de todos los snapshots|Etapa15, no atribuir garantía absoluta al término «original»|
| ConcurrenciaPG, caída real, respaldo y restauración con nueva tabla |Demostrar atomicidad fuera de excepciones simuladas|Costo medio; SQLite secuencial no prueba locks por fila. Revertir0009 elimina columnas/líneas históricas; no ejecutarlo sobre datos operativos sin estrategia de recuperación|Etapa15 pendiente|
| Constancia de merma, costo documentado desde físico0, volumen de Kardex |Completar evidencia de operación y rendimiento|Costo medio; contratos ya existentes. No sumar HUs por cada función auxiliar ni fijar SLA sin medición|Pendientes propios, no cerrados por regresión|

Se añade un caso escrito `CP-HU-INV-01a-003`; ninguna HU ni criterio se elimina. H1 no pretende reauditar íntegramente las etapas05/06/08/11/12. [Inventario](14-H-inventario.md) · [Informe](../ETAPA-14.md#vigente-14-h1).
