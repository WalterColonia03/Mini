# 03-AF / 05-E · Conciliación de carga inicial y respuesta perdida

11/11/2026, America/Lima. Sublote de conciliación completado. La etapa05 conserva estado parcial por despliegue y fronteras integrales; no se declara terminado otro módulo. El protocolo se leyó completo. No se encontraron AGENTS.md dentro del espacio inspeccionado. Se preservaron los cambios preexistentes.

## Fuentes, clasificación y matriz vigente

Se contrastaron HU-INV-01a, sus cinco CA (08:317–326), la adenda de autoría/constancia08:873, RN-01/03/14/19/29, tareas16:111–120 y la evidencia03-AB–AE. El inventario de campos, pantallas, límites, salidas, permisos y tareas inicial está en [03-AB](ETAPA-03-AB-recepcion.md); los cambios posteriores se identifican por corte. Los estados de sprint y las fuentes históricas conservan su función histórica. No se abrió ni modificó un XLSX, ausente en el entorno.

| ID / fuente / actor | Esperado → observado / ubicación | Estado, prioridad y acción |
|---|---|---|
| INV-01a/CA01,08:322; RN-01/29; ALMACENERO | Una carga directa por producto, permisos exclusivos. `initial_load_create`/`confirm_initial_load`: AB verifica 403 de ADMIN/VENDEDOR y carga; AE revalida disponibilidad; AF recupera la misma carga después de respuesta perdida. | CUMPLE en muestras. P1, conservar pruebas. Sesión vencida durante recepción no ejecutada en este conjunto. |
| INV-01a/CA02,08:323; RN-03; ALMACENERO | Normalización/duplicados, cantidad/costo/fecha válidos. `LotInputFormSet` y `_validate_lots`: AB límites y atomicidad; AC proveedor obsoleto, fecha Lima y aniversario20 años corregidos y verificados. | CUMPLE en muestras. P1. No se afirma cobertura exhaustiva de formatos o volumen máximo de filas. |
| INV-01a/CA03,08:324; RN-01; ALMACENERO | Rechazo completo y como máximo una carga concurrente. AB prueba inválidos/reenvío y PostgreSQL; AE carreras de desactivación; AF reenvío después de perder respuesta. | CUMPLE en muestras. P1. Caída del proceso/motor y recuperación posterior NO EJECUTADAS. |
| INV-01a/CA04,08:325; RN-14; ALMACENERO→VENDEDOR | Suma de cantidades y costo ponderado a cuatro decimales, visible con dos. AB18 unidades/costo3.0000 y consulta vendedor; AF1.23445→1.2345 y1.0050→S/1,01. | CUMPLE en muestras. P1. No acredita costos históricos de venta. Disponibilidad exige categoría/producto activos y lotes vigentes. |
| INV-01a/CA05,08:326; RN-19; ALMACENERO→venta de prueba | Lote con identidad, cantidad/costo/vencimiento e ingreso inmutable; FEFO total. AD protege modelo/SQL, verifica ambos motores y desempates vencimiento/ingreso/UUID. | CUMPLE en muestras. P1. Migración inventory0006 pendiente de despliegue. Relación persistente venta→lote sigue pendiente. |
| Adenda08:873; ALMACENERO/ADMIN | Constancia y autoría por lote/proveedor. AB verifica persistencia; AF recupera por menú y confirma acceso200 para almacenero/admin y403 para vendedor, tanto canónica como alias. | CUMPLE en muestras de constancia. Kardex completo permanece en08; no se deduce su aprobación. |

[Índice legible por máquina, hashes y resultados comprobados](../evidencias/03-AF-conciliacion.json). Los cinco estados CUMPLE describen muestras. No equivalen a garantía de ausencia de fallos.

## Auditoría inversa y tareas

La pantalla captura un producto por operación y hasta cuatro filas visibles de lote. El proveedor es opcional. La constancia muestra saldo/costo actuales junto a lotes de carga inicial y posteriores, y se recupera por «Ver inventario y alertas» → fila del producto → «Ver carga». El alias antiguo responde con la misma ficha y permisos. La persistencia mantiene la exclusión de una segunda carga por producto; no hay recuperación automática de una respuesta perdida que redirija por sí sola a la constancia.

| Tarea fuente16 | Evidencia / clasificación |
|---|---|
| S1-INV01A-UI | AB/AC/AE/AF, captura múltiple, mensajes, constancia y recuperación observadas con navegador automatizado. |
| S1-INV01A-VALID | AB/AC y regresión citada, validaciones servidor y roles. |
| S1-INV01A-TXDB | AB/AC/AE PostgreSQL y AD inmutabilidad; AF antes/después de respuesta perdida. |
| S1-INV01A-AUTO | Soportes y regresión conservados;38 controles nuevos AF. No se suman métodos repetidos como casos nuevos. |
| S1-INV01A-MAN | Existe ejecución visual con navegador automatizado. La sesión manual del responsable de sprint no se acredita mediante estas herramientas. |
| S1-INV01A-REV | Conciliación realizada aquí; no se atribuye una revisión independiente por otro integrante ni cierre histórico de DoD. |

**H-03AF-DOC01, P2, corregido.** La historia08:319 aún decía «producto enlatado», aunque DOC03-01 ya aprobó cualquier categoría activa, UND y vencimiento obligatorio. Se corrigió exclusivamente esa descripción y se agregó registro de procedencia en08. Sus cinco CA y la restricción RN-01 de reposición conservan su texto. La corrección no amplía a peso ni a productos sin vencimiento.

**AUD03AF-TEST01, tarea implementada/verificada.** Añadir al soporte aislado las dos interrupciones de transporte y recuperar por la interfaz. **PROP-03AF-REC01, mejora propuesta/P2:** ante respuesta incierta, ofrecer instrucciones para consultar inventario/constancia antes de repetir. El rechazo actual cumple CA03, pero su mensaje general no distingue por sí solo una carga anterior propia de otra restricción. No se implementó una clave de idempotencia ni una cabecera nueva por recepción.

## Nueva ejecución de navegador

Chrome157.0.8103.39, Django/SQLite aislados y tres roles: **38/38 comprobaciones**. La inyección de fallos se realizó interceptando exclusivamente el POST de carga inicial:

1. Antes de entregar el POST al servidor, se aborta con `connectionreset`: Chrome registra `net::ERR_CONNECTION_RESET`, la instantánea queda idéntica y el producto continúa elegible.
2. Se envía el POST mediante `route.fetch(maxRedirects:0)`, se observa302 del servidor y se aborta su entrega al navegador. Chrome vuelve a registrar el error de conexión; la base contiene una carga, dos lotes y dos unidades con proveedor/responsable correctos.
3. El mismo payload se reenvía autenticado: devuelve200 con error controlado y conserva toda la instantánea. Otra sesión de almacenero recupera el UUID existente desde el menú de inventario; recargar tampoco escribe.
4. Costos1.2344 y1.2345, una unidad de cada: promedio exacto1.23445, almacenado1.2345 (HALF_UP) y mostrado1,23. Otro producto con1.0050 conserva cuatro decimales y muestra1,01. Los lotes de la primera carga no cambian.
5. Ambas rutas de constancia permiten almacenero/admin y rechazan vendedor. Ninguna consulta altera el estado comercial.

[Comprobaciones y fallos de red observados](../evidencias/03-AF-af-recovery-20261111T173709141159Z-d8b1cd5f/browser.json) · [Captura inspeccionada de recuperación](../evidencias/03-AF-af-recovery-20261111T173709141159Z-d8b1cd5f/constancia-recuperada.png) · [Datos finales](../evidencias/03-AF-af-recovery-20261111T173709141159Z-d8b1cd5f/orm-final.json) · [Cierre](../evidencias/03-AF-af-recovery-20261111T173709141159Z-d8b1cd5f/result.json).

La interrupción se simula entre navegador y servidor; no se desconectó físicamente la red ni se detuvo el motor durante una transacción. No se probó este caso para reposiciones. No se utilizó teléfono. La evidencia anterior se revisó sin volver a ejecutar sus pruebas: AB79/PG3; AC29/PG4; AD24/PG3; AE29/PG4. La última regresión de aplicación sigue siendo346 métodos de03-AD, no repetida porque este corte no cambió código funcional.

## Conciliación de recepción y retiros

| Propuesta | Evidencia acotada / pendiente exacto |
|---|---|
| T01 | AA identifica unidad y caja desconocida; AB recibe tres productos en operaciones separadas. PARCIAL: conversión real de embalaje, envío/cabecera y atomicidad multiproducto sin selección de alcance. |
| T02 | Lecturas repetidas/alternadas y clasificación GTIN/interno tienen evidencia03-Y/Z y física previa. PARCIAL: la cámara no registra cantidades ni demuestra recepción de paquetes diferentes con igual código. |
| T03 | AB prueba lote repetido/normalizado y mismo número en artículos distintos. Muestra favorable; no equivale a trazabilidad de envío integral. |
| T04 | AB/AC prueban extremos, fechas y proveedor inactivo. Muestras favorables; proveedor retirado deja una mejora de identificación pendiente en04. |
| T05 | AB reenvío/recarga; AF pérdida de respuesta y recuperación de carga inicial. PARCIAL: caída de servidor/motor y respuesta incierta en reposición no ejecutadas. |
| T06 | AB cargas y entradas concurrentes; AC proveedor; L/M entrada posterior frente a desactivación; AE primera carga frente a desactivación. PARCIAL: recepción frente a baja y proceso integral siguen en08/15. |
| T11 | AB rechaza ADMIN/VENDEDOR al confirmar; AF comprueba consultas de constancia. PARCIAL: sesión vencida durante recepción y permisos de bloqueo/retiro fuera del ensayo. |

RN-01/DOC-03AB-01 conserva dos alternativas: seleccionar entrada directa con cambio explícito de regla o implementar solicitud aprobada con recepción total/parcial. La tecnología de lectura no decide esa política. Recepción multiproducto conserva alternativas de operaciones por producto o cabecera conjunta con política de todo/nada/parcial explícita. Cuarentena, motivos sanitarios, trazabilidad y comunicaciones no se consideran implementados por desactivar una ficha. Las propuestas T07–T10 conservan sus pendientes y revisión normativa16.

## Conservación y reproducción

El runner terminó con puerto cerrado, todos los archivos protegidos intactos y base original SHA256 `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`. Base nueva `datos/etapa03k-AF-20261111T173709141159Z-d8b1cd5f/audit.sqlite3`: tres productos, dos cargas, tres lotes; A2 unidades/B1/C0; cero ventas y turno ficticio OPEN. No se migró la base operativa. Los datos de prueba se conservaron.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03y_browser_run.py' af-recovery
```

La nueva corrida siempre prepara otra base marcada y verifica instancia antes de autenticar. Las evidencias históricas y sus errores de soporte se mantienen en sus carpetas. El índice consolidado selecciona las corridas finales pertinentes y no presenta los intentos anteriores como aprobados.

## Cursor exacto

**06-B / HU-INV-01b-CA02 y RN-28, frontera con11.** Preparar producto con dos lotes, vender unidades y guardar constancia/estado; registrar reposición que cambie el costo promedio y comprobar si cada venta conserva el costo aplicable al cobrar. Reproducir primero la brecha de03-Q en navegador y persistencia. Corregir únicamente el defecto inequívoco; no inventar costos de ventas antiguas. RN-01/DOC-03AB-01 mantiene su decisión independiente. Recepción multiproducto, caída de servidor, cuarentena y retiro siguen pendientes en sus traspasos.
