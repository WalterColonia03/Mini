# ETAPA 00 — Fuentes, vigencia y conservación del entorno

Captura inicial: **5 de noviembre de 2026, 14:46:30, America/Lima**. Revalidación: **9 de noviembre de 2026, 09:57:56, America/Lima**; repetida a las **10:12:49**, sobrescribiendo el JSON derivado con el mismo resultado. Este anexo inventaría archivos, procedencia documental, metadatos y cambios preexistentes. No ejecuta Django, pruebas funcionales ni flujos de usuario. El arranque y las comprobaciones del servidor se documentan en el informe principal.

## Evidencia reproducible y límites

- `ETAPA-00-fuentes-inventario.json`: captura original completa, con rutas por carpeta, fechas, hashes de archivos raíz, Git y metadatos OOXML del libro. El campo `generated_lima` conserva la fecha original.
- `ETAPA-00-fuentes-revalidacion-20261109.json`: comparación con aquella captura; conserva hashes iniciales y actuales, estado Git y control estructural del índice documental.
- `inventario_fuentes.py`: extractor de metadatos original. **No volver a ejecutarlo sobre la captura original si se quiere conservar la comparación del 5 de noviembre**, porque escribe ese mismo JSON.
- `revalidar_fuentes_00.py`: comparación de solo lectura de las fuentes. Reproduce la revalidación escribiendo únicamente su JSON de resultados. No consulta `.env`, contraseñas, tokens ni remotos Git.

Comando desde la raíz del proyecto:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/anexos/revalidar_fuentes_00.py'
```

Resultado del 9 de noviembre: **66 hashes iguales** a la captura inicial (17 archivos raíz y 49 archivos rastreados modificados), mismo HEAD y mismo estado Git. La igualdad sólo cubre los archivos efectivamente comparados; no certifica todos los archivos históricos ni el contenido de los 66 archivos no rastreados, que no tenían hash en la captura de fuentes inicial. El inventario de código dispone de su propia lista de hashes y límites.

## Mapa de carpetas y archivos

Los conteos siguientes pertenecen al inventario del 5 de noviembre. Excluyen `.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `.pytest_cache` y los archivos de entorno privado reconocidos por el extractor. Las rutas individuales están en la propiedad `directories` del JSON original. Son conteos de archivos inventariados, no de requisitos ni pruebas ejecutadas.

| Ubicación | Archivos | Papel y clasificación | Uso en esta etapa |
|---|---:|---|---|
| `r1-pmv/` | 178 | Sistema Django y pruebas disponibles; designado por `01_Proyecto_y_Releases.md:9`. | Fuente de implementación actual; inventario estático en anexo de código. Incluye 91 `.py`, 36 `.html` y 41 `.md`. |
| `EJEMPLO DE REFERENCIA MINIMARKET/minimarket-main/` | 158 | Proyecto de referencia separado; contiene JS/JSX y recursos web. | Inventariado por rutas/extensiones; no se ejecutó ni se trató como el sistema Django auditado. Su presencia no añade rutas al servidor R1. |
| `qr-minimarket/` | 1 | Un JPG. | Inventario de recurso visual; no es un segundo servidor. Su contenido no fue analizado en este sublote. |
| `archivo_historico_2026-10-08/` | 7 | Markdown histórico, fecha indicada en el nombre de carpeta. | Conservado como antecedente. Contenido completo NO EXAMINADO. |
| `linea_base_antes_codex_2026-10-09/` | 9 | Copias de documentos de la línea base anterior. | Conservadas; no sustituyen las fuentes de raíz. Ejemplo de estado antiguo: `04_Evidencias.md:7` dentro de esta carpeta se refiere al 8 de octubre. |
| `archivo_historico_jira/` | 21 | Material histórico: Markdown, imágenes, Word y configuración de ejemplo. | Jira excluido de evaluación por protocolo y `01_Proyecto_y_Releases.md:11`; no se abrió ningún servicio de Jira. |
| `prompts_sprint_1/` | 11 | Instrucciones y contratos del desarrollo de octubre. | Contexto histórico; las instrucciones antiguas de PR/Jira no se ejecutan como tareas actuales. |
| `auditoria_por_etapas/` | Paquete separado | Protocolo, prompts 00–17, nuevos resultados y scripts. | Fuentes de procedimiento y evidencias de esta auditoría; excluida del censo histórico de carpetas para evitar que el informe se cuente a sí mismo. |
| Archivos ZIP/RAR en raíz | 3 | `prompts_sprint_1_CORREGIDO_2026-10-12.zip`, `prompts_sprint_1_OBSOLETO_2026-10-10.rar`, `r1-pmv-integracion-sprint1.zip`. | Metadatos y hash inventariados; no extraídos ni usados para sobrescribir el trabajo. Contenidos internos NO EXAMINADOS. |

No se encontró `AGENTS.md` mediante `rg --files -g AGENTS.md` excluyendo dependencias y Git. La raíz de planificación no es un repositorio Git; `r1-pmv/.git` sí existe. No se concluye que no puedan existir otras instrucciones fuera de la raíz solicitada.

## Papel y vigencia de los documentos de raíz

| Fuente precisa | Papel observado | Vigencia para la auditoría |
|---|---|---|
| `01_Proyecto_y_Releases.md:3,7-11` | Plan de octubre con aviso actualizado el 5 de noviembre; señala requisitos, diseño histórico y código. | Orienta el mapa de fuentes. No acredita aceptación ni convierte Jira en requisito vigente. |
| `02_Diseno_Tecnico_R1_PMV.md` | Diseño R1 y matriz técnica; su papel histórico consta en `01:8`. | Contraste técnico, con diferencias registradas; no autoridad silenciosa ante conflicto. |
| `03_Matriz_de_Trazabilidad_y_Pruebas.md:3,5,7` | **Matriz histórica de Sprint 1: 9 HU y 41 CA.** | Objetivos de prueba históricos. No representa el producto completo ni una ejecución actual. |
| `04_Evidencias.md:3,5,32-47` | Registro histórico y validaciones de planificación. | Sus casillas y cifras se conservan como declaraciones de otra revisión; no se trasladan como resultados de esta etapa. |
| `07_Reglas_de_Negocio.md`, `08_Historias_de_Usuario.md`, `09_Product_Backlog.md` | Requisitos, reglas y trabajo futuro (`01:7`). `09:42,59,134` distingue selección, posteriores e ideas fuera. | Base de clasificación documental. El anexo de planificación enumera cada HU/CA/RN con referencia. |
| `14_Sprint_Planning.md`, `16_Task_Breakdown.md` | Plan y tareas históricos (`01:8`). | Contrastar alcance y dependencias; horas, tareas y marcas no equivalen a pruebas. |
| `20_Corte_De_Exposicion_Martes.md:3,7` | Exposición histórica de octubre, explícitamente no el plan actual. | No crea una fecha límite ni obliga a reproducir el cronograma. |
| `21_Alcance_Actual_y_Diferencias.md:3,5,23-29,42` | Guía con corte 5 de noviembre y resultados de otra ejecución. | Punto de partida; diferencias y resultados requieren su propia evidencia. No es una certificación integral. |
| `PLAN DE CHATGPT.MD:3` | Se declara ejecutado y sustituido como guía operativa el 9 de octubre. | Antecedente, no fuente de estado ni instrucciones activas para cargar Jira. |
| `REPORTE_CAOS_Y_UX_QA.md` y copia en `r1-pmv/` | Informe previo de escenarios/hallazgos. | Son **dos copias idénticas** por SHA-256 `dfd8e4b962ba92ae1d1d3b1974591cb6d306659b4e5390eef218893e99b1be10`, comprobado el 9 de noviembre; no dos ejecuciones independientes. |
| `r1-pmv/CONTROL_SPRINTS.md`, `AUDITORIA_USABILIDAD_05NOV2026.md`, `REPORTE_PRUEBAS_EXPLORATORIAS_05NOV2026.md`, `evidencias/` | Declaraciones históricas, guías y resultados previos. | Inventariados; una etiqueta «completada», «verificado» o «activo» requiere comprobación actual antes de promoverla a estado de auditoría. |

Las fechas de modificación del sistema de archivos no son fechas de aceptación. Los documentos principales de raíz se modificaron el 5 de noviembre entre las 14:21 y las 14:26 Lima; `PLAN DE CHATGPT.MD` figura modificado el 9 de octubre. Fechas y hashes individuales están en `root_files` del JSON original, sin inferir autoría.

## Libro de planificación: inventario previo a cualquier uso

`PLANIFICACION_SCRUM_R1PMV.xlsx` se examinó en dos cortes. El primero registró los metadatos OOXML. En el cierre de 00 se leyeron identificadores, ordinales, encabezados y estados declarados con `openpyxl` en modo de solo lectura. El hash se mantuvo entre apertura y cierre. Las fórmulas y el diseño visual quedan fuera de la revisión de procedencia.

| Propiedad | Evidencia observada |
|---|---|
| Tamaño | 26 323 bytes |
| Creación interna OOXML (`docProps/core.xml`) | `2026-11-05T05:10:21Z`, equivalente a 5/11/2026 00:10:21 Lima |
| Modificación interna OOXML | `2026-11-05T05:10:22Z`, equivalente a 5/11/2026 00:10:22 Lima |
| Modificación del archivo | 5/11/2026 00:10:22 Lima en la captura inicial |
| SHA-256 inicial y revalidado | `a9604b90d08dead7b815817f859004a802353aaf6f91f7e78a4467fa18406b49` |
| Hojas visibles (`xl/workbook.xml`) | `1. Resumen`; `2. HU y Criterios de Aceptación`; `3. Pruebas Unitarias`; `4. Product Backlog Pendiente` |
| Dimensiones OOXML declaradas | Hoja 1 `A1:E25`; hoja 2 `A1:H100`; hoja 3 `A1:G75`; hoja 4 `A1:E51` |

La hoja 2 identifica 28 HU como implementadas en tres sprints. La hoja 4 enumera 46 pendientes. Los conjuntos son disjuntos y su unión coincide con las 74 HU con CA de 08. Se localizaron 97 ordinales en la hoja 2 y cada par HU/ordinal coincide con el índice de 08 para esas 28 historias. Los textos completos de los criterios conservan su revisión semántica pendiente. La hoja 3 tiene 70 filas con un nombre `test_` en la columna C y declara 152 pruebas en A2. Esa cifra corresponde al registro histórico del libro. [Celdas y cotejo por ID](../evidencias/00-libro-cotejo.json).

La clasificación del libro corresponde a su propio corte. En `4. Product Backlog Pendiente!A4` figura HU-AUTH-02 como pendiente. La guía 21 y los servicios de identidad describen posteriormente el bloqueo de 15 minutos. La etapa 01 recoge esa diferencia. En A8 de la misma hoja aparece HU-USR-05, con reactivación candidata en el código, para la etapa 02. La aceptación de cada criterio se revisará en la etapa correspondiente. El cotejo se reproduce con [cotejar_libro_00.py](../soporte/cotejar_libro_00.py) y el Python con `openpyxl` del entorno de hojas de cálculo.

## Cambios preexistentes conservados

La captura y la revalidación coinciden:

- Rama local: `chore/S1-PLAT-01-walter-r1-pmv-import`.
- HEAD: `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, commit del 14/10/2026 17:53:58 −05:00, asunto `fix: align inventory and logout acceptance criteria`.
- **49 archivos rastreados modificados y 66 no rastreados.** La lista exacta está en `git.status` del inventario y en `status` de la revalidación.
- Entre los cambios rastreados hay configuración, modelos, servicios, formularios, pruebas, rutas, vistas, plantillas y estilos de los módulos de negocio. Entre los no rastreados hay migraciones, nuevas pantallas, informes y evidencias históricas.
- No se hizo commit, reset, checkout, stash, merge, limpieza ni restauración. La auditoría no atribuye esos cambios al trabajo de esta sesión.

**Clasificación:** `NO EXAMINADO` en cuanto a intención y aceptación del conjunto de cambios; inventario conservado y verificable. El HEAD no describe por sí solo el código observado, porque el árbol contiene modificaciones. Para reproducir un defecto debe conservarse el contenido concreto y su hash, además del commit.

## Control estructural del inventario documental

Se cotejó el JSON de planificación existente sin regenerarlo ni modificarlo. Resultado de metadatos del 9 de noviembre: 82 entradas de historias/ideas (74 activas y 8 fuera), 219 CA base con IDs únicos, 30 RN, 67 tareas con IDs únicos y 41 filas de matriz R1. Los IDs de CA de esas 41 filas coinciden con los CA de las 9 HU seleccionadas. Se resolvieron **514 referencias distintas de archivo y línea**; ninguna apunta a un archivo ausente o más allá de su longitud.

Esto comprueba identidad y ubicación, no el significado de cada enlace. Los 9 agregados QA del final de 08 se conservan separados de los 219 CA base por ambigüedad de IDs, como explica `ETAPA-00-conflictos-planificacion.md`. No se ejecutó ninguna prueba del sistema para producir estos conteos.

## Hallazgos, pendientes y siguiente cursor

| ID | Estado / prioridad | Evidencia y consecuencia | Próxima acción |
|---|---|---|---|
| FUE-00-01 | `CONFLICTO DE FUENTES` / P1 documental | 03 conserva matriz histórica y anexo con referencias/cifras de otra revisión; guía 21 y Control no coinciden en todos los alcances/estados. | Resolver por HU en su etapa, usando `ETAPA-00-conflictos-planificacion.md`; no sobrescribir resultados históricos. |
| FUE-00-02 | CONFLICTO DE FUENTES / P2 documental | Cortes diferentes del XLSX y de 21 para AUTH-02 y la reactivación USR-05 | Preservar la etiqueta histórica y comprobar cada comportamiento en las etapas 01 y 02. |
| FUE-00-03 | `NO EXAMINADO` / P1 reproducibilidad | Árbol Git con 49 modificaciones y 66 no rastreados anteriores. | Conservar el árbol; registrar hashes específicos al auditar cada caso. No atribuirlos a etapa 00. |
| FUE-00-04 | `NO EJECUTADO` / P1 evidencia | Cifras 95/126/152/163/202, 191 o 148 de informes anteriores describen otras ejecuciones y universos. | Sólo contabilizar una ejecución nueva cuando haya comando/herramienta, base, fecha, casos y resultado propios. |
| FUE-00-05 | `NO EXAMINADO` / P2 | Archivos comprimidos, Word e imágenes históricos/referencia censados sin revisar contenido completo. | Abrir sólo la fuente pertinente si una contradicción concreta lo requiere; no ampliar obligaciones desde documentos antiguos. |

**Cursor de este anexo:** inventario de procedencia y comparación de fuentes completados para este sublote. Continuar en el caso exacto del informe principal y `ESTADO_GENERAL.md`. El siguiente requisito documental de la cola es HU-AUTH-01/CA-01 (`08_Historias_de_Usuario.md:18`); sus pruebas funcionales y las de otros módulos no se consideran aprobadas por este anexo.
