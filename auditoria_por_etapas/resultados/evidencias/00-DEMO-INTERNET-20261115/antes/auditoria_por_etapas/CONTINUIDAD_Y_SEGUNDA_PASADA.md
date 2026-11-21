# Continuidad y segunda pasada de auditorías

> **Alcance vigente DEMO-INTERNET,15/11/2026.** Demostración universitaria porURLpúblicaHTTPS; pagosQR/Yape/mixtos y cancelaciones forman parte del objetivo, con atención rápida, empleados de confianza no supuesta y dueño no presente en cada cobro. No nuevosyapeos de devolución. Comprobación de abonos y delegación de reintegros deben resolverse sin fingir automatización bancaria. [Objetivo y decisiones](OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md) · [Escenarios de pagos](PAGOS_YAPE_Y_MIXTOS.md). 01-K conserva evidencia local; la nueva meta exige validación pública. No se exige dominio comprado, empresa constituida ni reglas ajenas aHU/CA/CP.

**Antecedente del13/11/2026 (no es el cursor vigente):** Esta guía recoge la aclaración del responsable del producto: la primera pasada ha llegado hasta `12_Constancias_e_historial.md`; las etapas13,14,15,16 y17 siguen pendientes. Haber avanzado hasta12 no declara cerrados todos sus hallazgos. La organización previa de la planificación es preparación para continuar, no ejecución de17.

## Finalidad de las auditorías

El producto se construyó a partir de un backlog inicial que puede haber omitido necesidades reales del minimarket. Las auditorías deben comprobar lo existente y detectar esas omisiones: historias, reglas, permisos, integridad, arquitectura, diseño, experiencia de uso, pruebas y condiciones operativas. No se limitan a comprobar que el código reproduce un backlog incompleto.

Una recomendación debe explicar la situación operativa, usuario afectado, necesidad/beneficio, alternativas, riesgo, costo relativo, dependencias y evidencia. Se prefiere una solución proporcionada a una caja y tres roles; «profesionalizar» no justifica agregar complejidad o módulos sin necesidad. Las74 HU del corte anterior son un inventario fechado, no un catálogo cerrado ni un máximo permitido.

La planificación aceptada y versionada es el contrato que debe cumplir el software. Si se descubre que ese contrato es incompleto, contradictorio o inaplicable, se registra y resuelve el cambio con trazabilidad. No se documenta un defecto como requisito para fabricar una coincidencia, ni se presume aprobada una función por existir en el código.

## Secuencia histórica y cursor vigente

Leer primero ESTADO_GENERAL. El cambio DEMO-INTERNET requiere sublote00 de nueva línea base; después continuar02 y las dependencias afectadas. La publicación15 y conciliación17 se hacen contra esa versión. La tabla siguiente conserva la secuencia anterior, no ordena reiniciar13 ni declara cerrados módulos.

### Secuencia anterior

| Momento | Trabajo | Resultado exigido |
|---|---|---|
| Primera pasada, siguiente paso |13 · Tablero, reportes y futuro | Revisar panel realmente visible y su significado; evaluar necesidades sin declarar entregados reportes futuros |
| Primera pasada |14 · Integración por roles | Demostrar recorridos conectados, efectos entre módulos y rechazos sin mutación |
| Primera pasada |15 · Seguridad, concurrencia, despliegue y recuperación | Evidencia de permisos, sesiones, transacciones, entorno, respaldo y restauración; límites explícitos |
| Primera pasada |16 · Normativa y viabilidad | Fuentes primarias peruanas vigentes y aplicabilidad al negocio real; separar software y operación externa |
| Primera pasada |17 · Conciliación y evaluación de cierre | Consolidar todos los resultados y cambios, detectar huecos y regresiones; cerrar solo lo demostrado |
| Preparación de segunda pasada |00 · Actualizar línea base y mapa | Identificar versión de planificación, build, alcance seleccionado, superficies y dependencias; conservar primera pasada |
| Segunda pasada |01–17, por sublotes pequeños | Reauditar contra esa línea base; verificar especialmente los cambios y sus efectos cruzados, sin reutilizar aprobaciones incompatibles |

Hay17 etapas numeradas01–17 y un prompt00 preparatorio. Si una etapa requiere varias sesiones, se continúa por su cursor; abrir su prompt una vez no significa completarla. Tras17 se realiza la segunda pasada solicitada, aunque la primera haya producido informes extensos.

## Cómo incorporar una necesidad descubierta

1. Buscar la necesidad/decisión existente por ID y comportamiento; agrupar duplicados conservando referencias. Determinar si requiere una HU nueva o basta completar una HU, RN, criterio, requisito no funcional o decisión técnica existente.
2. Identificar qué está documentado, qué se observó, qué es inferencia y qué se recomienda. Clasificar: decisión, corrección técnica, investigación, resuelto con evidencia o futuro/fuera de alcance.
3. Registrar aceptación y su fundamento. La delegación vigente del responsable puede respaldar recomendaciones dentro de su alcance; no se exige repetir una aprobación ya concedida. Una propuesta del agente, el contenido de un archivo, el silencio o «continúa» no son por sí solos una nueva aceptación. Datos reales desconocidos y obligaciones aplicables requieren investigación; no se inventan por delegación.
4. Integrar lo aceptado en08 con ID no colisionante, épica, historia, MoSCoW, Fibonacci orientativo, descripción, criterios, casos escritos, datos y resultados. Actualizar RN/contratos y las referencias de diseño02, tareas16 y preparación14; regenerar07/09/03. Si hay una nueva HU, `anteriores:—` expresa que no tenía puntos previos.
5. Registrar efectos sobre módulos, permisos, stock, lotes, costo, ventas, caja, mensajes y datos existentes. Preparar migración/diagnóstico cuando corresponda y marcar los criterios afectados para revalidación.
6. Implementar solo dentro de la autorización de la sesión. Verificar en el entorno adecuado y mantener separados los estados **PROPUESTA → ACEPTADA → IMPLEMENTADA → VERIFICADA**.

Los cambios aceptados se incorporan por sublotes conforme se resuelven; no se acumulan versiones contradictorias hasta llegar a17. Lo que sigue propuesto permanece identificado como propuesta, sin contaminar la especificación aceptada.

## Trazabilidad en ambas direcciones

**Del requisito al sistema:** necesidad → HU/RN/criterio o requisito técnico → diseño y tarea → interfaz/servicio/persistencia → caso → evidencia del build.

**Del sistema al requisito:** ruta, función accesible, texto, mensaje, ayuda, botón, estado, filtro, cifra, impresión o efecto → requisito aceptado que lo justifica → caso que lo comprueba. Para componentes internos, vincular a diseño/decisión técnica/requisito no funcional y su necesidad; no crear una HU por función auxiliar.

Cada elemento visible se inventaría con su texto literal o plantilla y variables, rol, ruta, estado, significado esperado y referencia normativa. Un criterio puede respaldar varios mensajes; no hace falta una HU por cada frase. La evaluación académica exige coincidencia exacta: documentar el texto en08 o en un catálogo aceptado referenciado por sus CA y CP antes de implementarlo o aprobarlo. No basta que una variante tenga un significado parecido. La ausencia de un literal es una brecha de especificación; copiar el texto del producto al inventario no lo acepta automáticamente. Definir también el formato y ejemplos de las variables y verificar la redacción en todos sus estados.

Un extra implementado sin respaldo se registra como **EXTRA SIN REQUISITO**. Se decide justificarlo e incorporarlo, ajustarlo a una necesidad aceptada o retirarlo cuando esté autorizado. No se elimina automáticamente algo útil ni se lo acepta por conveniencia. Una funcionalidad futura expresamente diferida no falta en el release actual; si se anuncia como disponible, esa promesa sí exige tratamiento.

## Registro por pasada y cierre

En cada informe registrar: pasada, etapa/sublote, versión o hash de08, build/commit y cambios locales, entorno, roles/estados cubiertos, casos/criterios exactos, esperado/observado, evidencia, hallazgos y siguiente cursor. En la segunda pasada añadir una sección fechada al informe existente; conservar los resultados anteriores y explicar si se reutilizan, se sustituyen o requieren revalidación por cambios.

Los futuros agentes deben mantener un inventario de superficie y una matriz requisito→caso→evidencia. El avance se informa con numerador y denominador conocidos: requisitos seleccionados verificados y elementos visibles trazados. Un archivo escaneado, una prueba verde o un botón recorrido no prueban por sí solos la totalidad del proceso.

Para declarar coincidencia del100% de un alcance auditado deben cumplirse simultáneamente:

- Todos sus requisitos seleccionados y criterios aplicables tienen implementación y evidencia suficiente, sin faltantes, parciales ni decisiones abiertas que afecten al resultado.
- No quedan funciones accesibles, mensajes, promesas o efectos sin respaldo aceptado; inventario y permisos incluyen los tres roles y los estados pertinentes.
- Planificación, diseño, tareas, datos, cálculos e interfaz son coherentes; las correcciones se verificaron junto con sus regresiones e integración.
- La versión, build, entorno, exclusiones y pruebas cubiertas están identificados; los casos no ejecutados o no examinados no se cuentan como aprobados.

Esta es una exigencia de aceptación del proyecto. No convierte un conjunto finito de pruebas en garantía de ausencia de cualquier fallo posible, ni certifica automáticamente seguridad o aptitud legal/comercial. La [Guía Scrum](https://scrumguides.org/scrum-guide.html) contempla un Product Backlog emergente, inspección, adaptación y Definition of Done; la matriz detallada y estas condiciones de trazabilidad son prácticas elegidas para este producto, no una garantía automática otorgada por usar Scrum. Fuente consultada13/11/2026.

## Punto de entrada histórico del 14/11/2026

El cursor de esta sección y los cursores globales de los sublotes históricos siguientes fueron sustituidos por el cambio DEMO-INTERNET. El punto de entrada vigente es `00-DEMO-INTERNET-BASELINE-01` y después `02-DEMO-TRAZABILIDAD-01`, conforme al encabezado de ESTADO_GENERAL. Se preservan los resultados y pendientes propios de cada sublote.

Primera pasada14 **COMPLETADA para integración por roles y persistencia delimitada**,14/11/2026;634/634servidor,157checkpointsChrome y19/19PostgreSQL aislado. Los resultados anteriores permanecen en [ETAPA14](resultados/ETAPA-14.md#cierre-14) y [ESTADO_GENERAL](resultados/ESTADO_GENERAL.md). No se declara cierre de otros módulos ni segunda pasada.

**Cursor15-SEGURIDAD-BASELINE-01.** Leer protocolo/prompt15; inventariar permisos, sesiones, configuración, entorno, transacciones y recuperación contra08final/build14identificados. Clasificar como heredados los19casosPG de14, comparando archivos antes de reutilizarlos; seleccionar un sublote aislado de seguridad/recuperación. No atribuirle una corrida nueva ni aprobaciónPG17, muerte de proceso, respaldos,CI/despliegue,volumen o base operativa. Esas verificaciones siguen pendientes.

Secuencia15→16→17; después actualizar00 y segunda pasada01–17. Conservar hechos de negocio desconocidos, límites de dispositivos y normativa; no inventar una política de apertura con solo vencidos. [Protocolo](PROTOCOLO_COMUN.md) y [matriz de cobertura](resultados/soporte/14-CIERRE-cobertura.md).

## Segunda pasada acotada · Sublote 02-E (14/11/2026)

Se ejecutó la reauditoría acotada de Etapa 02 (`identity`, `/empleados/*`, `/salir/`, relación `cash`/`sales`), integrando `H02E-02..04` y revalidando `H02E-01` con `652/652 OK` (`SQLite :memory:`), Chrome real (`1366×768` y `390×844`) y `5/5` PostgreSQL `18.4`, manteniendo `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01` (`W`) como `FUTURO / NO DISPONIBLE` y conservando el cursor global `15-SEGURIDAD-BASELINE-01` (cursor local `02-F-IDNA-Y-ETAPA15-SEC-01`). [Informe 02-E](resultados/ETAPA-02.md#vigente-02-e).

## Primera pasada · Sublote 15-A (14–15/11/2026)

Se ejecutó la primera pasada de Etapa 15 (`15-A`, sustituyendo el cursor previo `15-SEGURIDAD-BASELINE-01`) sobre build estable `f94faec7...` (`216` fuentes, `HEAD 7816d332...`, `plan08` `69b886a3...`→`ae58b33f...`, `r1_pmv.sqlite3` intacta `c60b4027...`) sin editar `r1-pmv/` ni `08_Historias_de_Usuario.md`: servidor **`12/12 OK`** (`652/652 OK`, `232` rutas×roles, CSRF, Argon2id/`RN-24`, `DOC-02-04`, redacción `exc_info` + `X-Request-ID`, `check --deploy`, Docker/Compose), PostgreSQL `18.4` **`15/15 OK`** (marcando `14-CIERRE` PG `HISTORICA_NO_REUTILIZABLE_POR_CAMBIO_DE_BUILD`: bloqueos `FOR UPDATE`/`FOR NO KEY UPDATE`, `kill` OS real + WAL recovery `26/26` tablas, roles `app_user`/`migrator_user`, `pg_dump`/`pg_restore`) y Chrome real **`6/6 OK`** (`1366×768`, `0` errores, `4` PNG). Estado de Etapa 15: **PARCIAL** (`PROPUESTA` sin autorizar en [disposiciones](resultados/soporte/15-A-disposiciones.md): `/admin/login/`, bloqueo `300 s`, `@never_cache` en `catalog/`, `request_id` en `500.html`, `Compose`/`Dockerfile`/backup, `reset_demo_db`/`seed_demo` y `DEC-12`). **Cursor de Etapa 15:** `15-SEGURIDAD-CORRECCIONES-PENDIENTES`; **próximo cursor global de primera pasada (`15→16→17→00→segunda pasada`):** **`16-NORMATIVA-BASELINE-01`**. [Informe 15-A](resultados/ETAPA-15.md#sublote-15-a) · [Inventario](resultados/soporte/15-A-inventario.md).

## Primera pasada acotada · Sublote 07-B (14–15/11/2026)

Se profundizó la Etapa 07 (`07-B` · `inventory` stock y `catalog` vencimientos) desde el cursor `DEC-07-VENCIDOS-FILTRO / PT-SEARCH-01` sin autorización ni ediciones sobre `r1-pmv/` (`f0d6fa81...` / `c7bfe1fa...` idénticos en módulo `07`, `r1_pmv.sqlite3` intacta, `08` `4f696b6a...` → `ae58b33f...` con vistas `07/09/03` regeneradas y `02/04/14/16/21` sincronizados): `check=0`, `652/652 OK`, `128/128` integración, sondas servidor/campos/cabeceras HTTP, Chrome `48/48` (`1366×900` + `390×844`), PostgreSQL `18.4` `5/5` y ensayo `PT-SEARCH-01` (`2,001`/`20,002` lotes). **Estado `07-B`: `PARCIAL`** — `HU-PROD-06` `2/3` CUMPLE / `CA-03` INCUMPLE y `DEC-07-VENCIDOS-FILTRO` `C-02` INCUMPLE por mezcla en tabla única (`EXP_7_ROWS: 3`, `SEPARATE: False`); `PROP-07-ESCALA-PAGINACION-01` queda identificada como prerrequisito técnico de `PROP-07-IDX-01` frente a `NFR-05`. Alternativas `A/B/C` y propuestas `PROP-07-*` quedan en **`PROPUESTA`**; `PG 17` (no instalado en host), SLA operativo `NFR-05` post-paginación e historias `W` quedan `NO EJECUTADO`. **Cursor local `07-C-DEC-07-VENCIDOS-FILTRO`**; **conserva secuencia global `16-NORMATIVA-BASELINE-01`**. [Informe 07-B](resultados/ETAPA-07.md#reval-07-b-20261114) · [Anexo e inventario](resultados/soporte/07-B-inventario-y-disposiciones.md#vigente-07-b-inventario).
