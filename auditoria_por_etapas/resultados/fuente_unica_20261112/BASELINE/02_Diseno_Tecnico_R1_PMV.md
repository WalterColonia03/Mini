# 2. Diseño técnico vigente y brechas de implementación

> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/02_Diseno_Tecnico_R1_PMV.md). Jira no forma parte de este seguimiento.

## 2.1 Arquitectura y alcance

Monolito modular Django5.2/Python3.12, plantillas y servicios transaccionales, una caja física, tres roles exclusivos. PostgreSQL17 sigue motor objetivo; la suite actual usa SQLite aislado y existen muestrasPG18.4, sin equivalencia automática de concurrencia/versión. No se cambian dependencias, infraestructura ni bases en esta conciliación.

Alcance vigente33 HU de09 más contratos de ENCARGOS. Lo especificado aquí es diseño requerido, no inventario de tablas ya implementadas. Las simulaciones de seis Developers y fechas/216h/67tareas quedaron en BASELINE y no acreditan equipo, capacidad o aceptación real.

## 2.2 Responsabilidad de capas

Plantillas ayudan con formularios/foco/mensajes; vistas autentican/validan forma y llaman servicios; servicios reautorizan, validan reglas y manejan transacciones/locks; modelos/BD protegen tipos, FK, unicidad y checks. Ninguna cifra, rol, vendedor/turno o estado enviado por el navegador es autoridad. GET no muta datos de negocio.

La aplicación usa HTML y formularios Django. El contrato existente devuelve errores de campo mediante200 cuando corresponde y redirige tras POST válido;401/409/422 de un diseño API previo no se exigen a todas las vistas HTML. Navegación anónima redirige al ingreso; rol ajeno deniega403 y propiedad puede ocultarse con404. No exponer SQL/stack/secretos. El mismo rechazo debe conservar datos independientemente del códigoHTTP.

## 2.3 Modelo e invariantes

Identidad/catálogo/inventario/caja/ventas mantienen FK y datos históricos. Código de producto editable no cambia identidad ni snapshots. GTIN y código interno conservan equivalencias/reservas ya aceptadas; legacy ambiguo requiere clasificación antes de migrar. Nombre comercial normalizado único incl.inactivos, empleados/proveedores pueden ser homónimos. Todos los productos del alcance sonUND con vencimiento.

Una carga inicial por producto; recepciones posteriores separadas por identidad/clave/huella, no compartiendo la constancia de carga como si fueran el mismo evento. Una recepción por producto puede tener varios lotes; multiproducto/SOL futuros. Número comercial normalizado no es UUID de ingreso: permitir recepciones distintas del mismo lote coherente con fecha/costo/proveedor propios (DOC03AI). Ajuste de existencia vencida soloADMIN y no vendible; ninguna entrada ordinaria vencida.

Venta confirmada requiere cabecera, líneas ordenadas, snapshots producto/precio/costo/vendedor/caja, asignaciones por lote, movimiento de efectivo y de inventario, correlativo y resultado idempotente atómicos. El código actual no implementa todas esas garantías: asignaciones y snapshots vendedor/caja son brechas; tampoco se atribuyen tablas genéricas por analogía. Se permiten estructuras equivalentes más simples si preservan cada garantía con evidencia. DraftLine retenidas no sustituyen asignaciones históricas.

RN25 exige venta irrepetible; clave UUID y huella canónica pueden vivir en la entidad confirmada con unicidad y controles de actor/contenido, sin obligación de tabla genérica `idempotency_record`. Misma clave/contenido devuelve original; distinto contenido rechaza. No se requiere cabeceraHTTP si el formulario existente transporta una clave validada con las mismas garantías.

## 2.4 Autorización y exposición

RN29 y DEC12PERMISOS son la matriz única: ADMIN mantiene maestros/personal, ajusta inventario, registra bajas y consulta global; ALMACENERO recibe/da de baja y consulta inventario; VENDEDOR opera solo su turno y consulta propios. Portal técnico no se concede por rol comercial. Históricos/constancia cliente no exponen costos. La normalización/máximo254 y reset trazable de personal se detallan en DOC02-04; no confundir resetADMIN con recuperación por correo futura.

## 2.5 Dinero, costo, tiempo y datos

Dinero Decimal2, costo Decimal4, HALF_UP. RN14 usa físico registrado para promedio móvil, no stock vendible. Venta/baja/ajuste negativo no reponderan por costos de compra restantes; al agotar físico, promedio vigente0 y snapshots previos intactos. Entrada actualiza ponderado, ajuste positivo sigue su política explícita. Costos legacyNULL permanecen desconocidos salvo evidencia inequívoca.

Límite operación venta/efectivo/apertura9,999,999.99; cierre acumulado admite14,2; diferencia=contado−esperado y puede ser negativa. Nuevo descuento discrecional deshabilitado como requisito pendiente de código; históricos permanecen. Base=HALF_UP(total/1.18,2),IGV=total−base describe modelo interno uniforme, no certificación tributaria.

Timestamps UTC, negocio/pantalla America/Lima. Físico suma disponible; vendible requiere fecha>hoy y disponibilidad comercial de producto/categoría. FEFO total fecha→ingreso→ID. No usar CHECK dependiente del reloj. Referencias históricas no se reconstruyen con datos maestros actuales.

### Restricciones e índices mínimos

| ID | Restricción o índice | Motivo |
|---|---|---|
| `DB-C01` | `UNIQUE(account.email_normalized)` | Login inequívoco |
| `DB-C02` | `UNIQUE(category.name_normalized)` | Seed idempotente y sin categorías duplicadas |
| `DB-C03` | `UNIQUE(product.barcode_normalized)` | Código de barras irrepetible |
| `DB-C04` | checks de precio `> 0`, mínimo `>= 0`, costo `>= 0` | Integridad aunque se evada el formulario |
| `DB-C05` | `UNIQUE(initial_inventory_load.product_id)` | Impide segunda carga inicial, incluso concurrente |
| `DB-C06` | Unicidad de línea/lote normalizado dentro de recepción; identidad comercial puede repetirse en otra recepción (DOC03AI) | Alcance de unicidad del lote acordado |
| `DB-C07` | Cantidad recibida original>0 e inmutable; saldo disponible>=0; costo>0; capacidad acumulada y movimientos de ajuste separados del original recibido | No confundir cantidad original recibida con capacidad tras ajuste positivo; conciliar saldo con movimientos |
| `DB-C08` | Índice FEFO candidato por producto/vencimiento/ingreso/ID; medir antes de crear o cambiar | Selección estable de lotes vendibles |
| `DB-C09` | índice único parcial de `cash_shift(register_id)` donde estado=`OPEN` | Una sola caja abierta bajo carrera |
| `DB-C10` | índice único parcial de `sale_draft(shift_id)` donde estado=`ACTIVE` | Un borrador activo observable |
| `DB-C11` | Correlativo venta único; clave idempotente única por operación en registro propio o entidad confirmada equivalente, con actor y huella verificados | Correlativo e idempotencia |
| `DB-C12` | `UNIQUE(cash_movement.sale_id)` cuando hay venta | Un cobro no suma dos veces a caja |
| `DB-C13` | índices de búsqueda por código, nombre normalizado, turno/fecha de venta y vencimiento | Volumen de referencia y consultas del flujo |
| `DB-C14` | FK restrictivas desde ventas, detalles, asignaciones, lotes y turnos | Protege historial |
| `DB-C15` | `CHECK(role.code IN ('ADMIN','ALMACENERO','VENDEDOR'))` | Impide roles fuera de los tres autorizados en R1 |
| `DB-C16` | `CHECK(product.controls_expiration = TRUE)` en R1 | Impide producto sin control de vencimiento en alcanceUND |

La condición «vencimiento posterior al día actual de Lima» y las sumas entre filas no se expresan como `CHECK` dependiente del reloj. Se validan dentro del servicio transaccional con un reloj inyectable y se cubren con pruebas de integración. Las restricciones simples sí viven en PostgreSQL.

## 2.6 Transacciones y orden de locks

El diseño anterior omitía locks de actores incorporados por auditorías. La implementación siguiente debe documentar un orden global compatible con todas las rutas (actor, caja/turno, borrador, producto/lote, contador/derivados), ordenando conjuntos de IDs; no copiar la secuencia histórica de un solo servicio. `PROP-09-LOCK-ORDER-01` y `SEC-15-CONC-02` requieren verificar parejas de operaciones y ausencia de inversiones. La unicidad en BD sigue siendo barrera final. No se considera probado solo por usar `atomic()`.

Idempotencia no habilita leer venta ajena ni aplicar política nueva a una confirmación histórica. Cobro/cierre comparten exclusión de turno; venta/recepción/baja/ajuste comparten producto/lotes y actor revalidado. El resultado concurrente debe corresponder a un orden serial válido. Fallo en cualquier derivado revierte operación completa; reintentos técnicos limitados solo ante error transitorio comprobado, nunca ante validación de negocio.

## 2.7 Contratos web y presentación

Rutas reales se consultan en urls.py y matrices de etapa. Superficies principales: ingreso/salida, empleados, categorías/productos, proveedores, carga/entrada/stock/vencimientos/bajas/ajustes/movimientos, apertura/cierre/turnos, borrador/cobro/constancia/historial. No prometer endpointsREST del diseño histórico ni pantallas de funciones futuras.

Encargos define campos/límites, confirmación de estado, error contextual, consulta propia/global, orden persistido, paginación25 y no mutaciónGET. Pantalla bloqueada tras300s requiere servidor+reautenticación, preserva borrador/turno y no es logout ni bloqueo de ingreso15min. Etiquetas, teclado, foco, ancho estrecho e impresión requieren prueba visual propia.

## 2.8 Seguridad y eventos

Sesión de servidor, rotación/revocación, Argon2id, CSRF en escrituras, HTTPS/cookies seguras en red, permisos dentro del caso de uso, secretos fuera de repositorio y logs sanitizados. Son controles requeridos; configuración productiva no examinada. Portal técnico restringido; tráfico/retención requieren medir entorno y fijar política explícita. No confundir mensajes uniformes con prueba estadística de tiempos ni filtro con evento instrumentado. Contratos DOC01-06 y DOC02-04.

## 2.9 Legado y migración

Cada encargo produce diagnóstico de colisiones, referencias, valores, origen y cobertura histórica antes de migrar. Carga/entrada de una misma familia, costosNULL, orden de líneas antiguo y asignaciones faltantes necesitan tratamiento específico. No inventar historia, fusionar maestros ni actualizar datos del usuario en este trabajo. Preservar migraciones aplicadas; nuevas restricciones requieren ensayo sobre clon y rollback. `sales.0004` añade producto; `sales.0005` añade costo unitario.

## 2.10 Migraciones y datos iniciales

- Las migraciones Django son versionadas, revisadas y aplicadas en CI/entorno autorizado; la base operativa requiere autorización separada; no se modifica una migración que ya llegó a demostración.
- `RunSQL` se usa solamente para índices parciales, checks o triggers justificados, con operación inversa cuando sea segura.
- CI crea PostgreSQL vacío, ejecuta todas las migraciones, aplica seeds dos veces y confirma que la segunda ejecución no duplica filas.
- El comando idempotente de datos ficticios crea roles, tres cuentas activas de prueba (una por rol) y una cuenta inactiva de prueba, categoría «Productos enlatados», caja `CAJA-01` y contador inicial. Las contraseñas proceden del ambiente y no del repositorio.
- El reset de prueba solo puede ejecutarse en ambientes marcados expresamente como `local` o `ci`; debe negarse en demostración.
- No se cargan productos, lotes, ventas ni cierres ficticios como si fueran evidencia del Sprint. Los fixtures de prueba permanecen identificados como tales.

## 2.11 Ambientes, CI y despliegue

| Ambiente | Datos | Acceso | Propósito |
|---|---|---|---|
| Local | Fixtures ficticios reiniciables | Equipo | Desarrollo y prueba individual |
| CI | PostgreSQL efímero por ejecución | Pipeline | Migraciones, análisis y pruebas automáticas |
| Demostración | Datos ficticios controlados | HTTPS y equipo autorizado | Revisión integrada y Sprint Review |

### Pipeline obligatorio

1. Instalación reproducible de dependencias fijadas.
2. Formato/lint y comprobaciones estáticas.
3. `python manage.py check --deploy` con configuración de demostración segura.
4. Base vacía → migraciones → seeds dos veces → comprobación de drift.
5. Pruebas unitarias e integración con el runner estándar `python manage.py test`; los soportes aislados de auditoría pueden invocar el runner estándar sin reemplazar sus tests ni excluir módulos.
6. Pruebas de concurrencia e idempotencia contra PostgreSQL real, no SQLite.
7. Construcción de imagen identificada por commit.
8. Playwright del recorrido crítico en ambiente efímero o de integración.
9. Publicación del artefacto solo si todas las puertas anteriores terminan correctamente.

### Despliegue y reversión

- El despliegue de demostración es manual y autorizado desde un artefacto ya comprobado en CI.
- Antes de una migración con datos se crea backup y manifiesto.
- Se aplica migración una sola vez, se inicia la nueva imagen y se ejecuta smoke test: `ready`, login, lectura de categoría y acceso autorizado.
- Si falla la aplicación, se vuelve a la imagen anterior. No se autoriza migración destructiva por esta conciliación; los cambios de esquema son aditivos para permitir reversión de aplicación o, en caso extremo, restauración controlada.
- La base no expone puerto público. HTTPS es obligatorio si el enlace sale del equipo local.

## 2.12 Observabilidad y auditoría

- Logs estructurados con UTC, nivel, evento, `request_id`, usuario interno cuando exista, módulo, duración y resultado.
- Cada respuesta de error muestra un `request_id` que permite correlacionar sin revelar internals.
- Eventos mínimos: login exitoso/fallido sin contraseña, logout, producto creado/rechazado, carga confirmada/rechazada, apertura/conflicto, cobro/rollback/reintento idempotente y cierre/conflicto.
- Métricas mínimas del host: disponibilidad de aplicación, conexión a BD, latencia y conteo de respuestas 5xx. Observabilidad avanzada queda fuera del PMV.
- El registro de auditoría no sustituye las evidencias de prueba y no se marca como implementado hasta existir una ejecución real.

## 2.13 Backup y restauración

### Backup (`S1-OPS-DB-01`)

1. Ejecutar `pg_dump` en formato custom, sin propietarios ni credenciales embebidas.
2. Nombrar el archivo con ambiente y timestamp UTC.
3. Generar manifiesto con versión PostgreSQL, commit, última migración, tamaño y conteos de control.
4. Calcular SHA-256 y almacenarlo junto al manifiesto.
5. Guardar la copia cifrada fuera del repositorio y del volumen activo de PostgreSQL.
6. Conservar 7 diarias y 4 semanales. Es objetivo de retención del diseño; no se ha ejecutado ni autorizado eliminación operativa.

### Restauración (`S1-OPS-DB-02`)

1. Crear una base limpia aislada con la misma versión mayor.
2. Verificar checksum antes de restaurar.
3. Ejecutar `pg_restore`, comprobar migraciones y ejecutar checks de integridad.
4. Comparar conteos del manifiesto y verificar correlativos, un turno, productos, lotes y una constancia histórica.
5. Ejecutar el recorrido de smoke test sin afectar demostración.
6. Registrar duración y resultado real en `04_Evidencias.md`; hasta entonces el estado es `Pendiente`.

Objetivos propuestos para el piloto: **RPO máximo 24 horas** y **RTO máximo 2 horas**. La puerta de piloto exige una restauración real satisfactoria, no solo la existencia de un archivo.

## 2.14 Requisitos no funcionales de R1-PMV

| ID | Requisito verificable | Método previsto |
|---|---|---|
| `NFR-01` | Ninguna operación transaccional deja venta, stock, caja o carga a medias | Fallos inducidos e inspección posterior |
| `NFR-02` | Doble solicitud no crea dos cargas, turnos, ventas, correlativos ni cierres | Pruebas concurrentes con barrera |
| `NFR-03` | Toda operación protegida rechaza sesión ausente, rol incorrecto y URL directa | Matriz de autorización automática/manual |
| `NFR-04` | Dinero usa decimal exacto; `base + IGV = total`; stock nunca es negativo | Pruebas de frontera y constraints |
| `NFR-05` | En volumen de referencia, búsqueda responde en ≤ 2 s p95 y cobro en ≤ 3 s p95 en el host de demostración acordado | Ensayo repetible, ambiente y muestra registrados |
| `NFR-06` | Flujo principal operable con teclado, foco visible, etiquetas y mensajes asociados al campo | Revisión manual y Playwright básico |
| `NFR-07` | Compatible con Chrome estable en Windows 10/11 a 1366×768 como mínimo; una comprobación en Edge queda como uso de reserva, no como puerta de R1 | Matriz manual registrada |
| `NFR-08` | Instalación, migración, seeds y build son reproducibles desde un clon limpio | Pipeline y guía repetida por otro Developer |
| `NFR-09` | Logs permiten correlacionar fallos sin incluir secretos ni datos sensibles | Inspección de logs de casos positivos/negativos |
| `NFR-10` | Backup cumple checksum/retención y restore recupera el recorrido en ≤ 2 h | Ejecución separada de backup y restore |
| `NFR-11` | Fechas se almacenan en UTC y reglas de vencimiento/visualización usan Lima | Pruebas alrededor de medianoche de Lima |
| `NFR-12` | Una venta y constancia confirmadas permanecen inmutables aunque cambien datos maestros | Consulta histórica después de modificar fixture maestro |

Los umbrales de rendimiento son una línea base de aceptación para la demostración, no una promesa de producción. El reporte debe incluir equipo, versión, datos, número de ejecuciones y percentil; una afirmación sin esos datos no constituye evidencia.

## 2.16 Puertas técnicas

Antes de comenzar una Story:

- sus CA y RN están trazados en `03`;
- las decisiones necesarias de esta línea base están ratificadas;
- existen contratos o fixtures que permitan trabajo paralelo;
- la Task/Subtask tiene resultado y evidencia esperada.

Antes de marcar una Story como Hecha:

- migraciones aplican desde base vacía;
- autorización, servicio y constraints relevantes están comprobados;
- pruebas automáticas y manuales asociadas tienen resultado real;
- un revisor distinto comprobó sus CA;
- no existen Bugs críticos/graves abiertos;
- `04_Evidencias.md` enlaza evidencia real, no una descripción futura.

Antes del piloto controlado, además:

- el recorrido E2E completo es satisfactorio;
- el despliegue y smoke test son satisfactorios;
- backup y restauración se ejecutaron por separado con checksum válido;
- la constancia exhibe la advertencia tributaria;
- existe autorización académica/documentada antes de un piloto, si el curso lo permite.

## 2.17 Exclusiones vigentes

SOL, anulaciones/Yape/fiscalidad, multirrol/múltiples cajas/sedes, productos sin vencimiento o por peso, correo/sesión única/cierre remoto/LOG UI, caja manual/forzada/aprobada y reportes completos permanecen futuros o fuera según09. Mermas, recepción directa, personal y bloqueo de ingreso sí están seleccionados; pantalla300s es nueva puerta del piloto. No ocultar esas brechas bajo exclusiones históricas deSprint1.

## 2.18 Compatibilidad y evidencia

Versiones exactas ejecutadas y hashes están en VERIFICACION.md; compatibilidad esperada y política de soporte en FUENTES_EXTERNAS.md. CI, backup/restore, NFR05/10 y despliegue continúan pendientes de evidencia adecuada. Un dry-run sin migraciones nuevas no demuestra migraciones aplicadas a la base operativa.

## 2.19 Trazabilidad de decisiones técnicas DT

Los IDs originales se conservan; sus formulaciones vigentes son las siguientes. No son evidencia de ejecución.

| ID | Decisión vigente | Aplicabilidad |
|---|---|---|
| DT-01 | Web interna responsiva, mismo origen | Conservada; pruebas visuales por alcance |
| DT-02 | Monolito Django5.2/Python3.12, templates;HTMX opcional | Python3.12.10/Django5.2.18 ejecutados; otras versiones no acreditadas aquí |
| DT-03 | PostgreSQL17 objetivo y migraciones nativas | 18.4 evidencia parcial; no actualizar motor sin plan |
| DT-04 | Tres roles exclusivos;3cuentas activas +1inactiva ficticia | Alineado con seed_pmv; ninguna cuenta/rol real inferido |
| DT-05 | Sesión servidor, cookies seguras/CSRF/Argon2 | Despliegue real no verificado |
| DT-06 | Cualquier categoría activa,UND,vencimiento; ajuste vencido excepcional no vendible | DOC03-01 y RN03 vigente |
| DT-07 | Lote normalizado y recepción propia;FEFO fecha/ingreso/ID | DOC03AI/DEC05ESPACIOS sustituyen unicidad global producto+número |
| DT-08 | Decimal2/4,HALF_UP; costo móvil físico y topes separados | RN14 y DEC11TOPE; fiscalidad real pendiente |
| DT-09 | Salir conserva turno; descarta borrador con confirmación | RN30; bloqueo pantalla es otro flujo |
| DT-10 | Caja única y turnoOPEN global único | Permisos/locks/constraint y pruebas concurrentes |
| DT-11 | BorradorACTIVE solo con líneas, sin reserva | GET no muta; cantidad1..999999 |
| DT-12 | V-00000001 global único, ascendente e inmutable | Idempotencia y atomicidad completos |
| DT-13 | Local,CI efímero,demostración; redBD privada | DockerCompose del diseño no acredita despliegue real |
| DT-14 | Backupcustom/manifiesto/SHA256;7diarias+4semanales;restore aislado | Objetivo de diseño, sin eliminación operativa ni restauración verificada aquí |
| DT-15 | Volumen de referencia2,000productos/20,000lotes/300ventas-día | PruebasNFR05 pendientes; no estimación de actividad real |
