# ETAPA 00 — Índice de planificación

Fecha: 5 de noviembre de 2026 (America/Lima). Método: lectura del protocolo completo y extracción estática de identificadores con referencias; sin ejecución de HU, CA ni pruebas funcionales. Ningún estado histórico se convierte en aprobación actual.

Este índice se regenera con `python auditoria_por_etapas/scripts/inventariar_planificacion.py`. Las citas son rutas relativas a la raíz del proyecto y números de línea. El JSON adjunto conserva un registro individual por criterio y sus referencias. La evaluación semántica en profundidad se reserva a las etapas correspondientes.

## Alcance y papel de las fuentes

| Fuente | Papel / vigencia |
|---|---|
| 01_Proyecto_y_Releases.md:3,7-11 | Plan histórico de octubre; identifica 07/08/09 como requisitos y futuro, r1-pmv como código. Jira retirado. |
| 02_Diseno_Tecnico_R1_PMV.md:26,80,349 | Diseño histórico R1; DT-01..15 y NFR-01..12. La matriz de constancias fue actualizada y debe conciliarse con RN-29. |
| 03_Matriz_de_Trazabilidad_y_Pruebas.md:3,5,7,271 | Matriz histórica de R1: objetivos de prueba y anexo QA histórico; no lista completa del producto ni evidencia de esta ejecución. |
| 07_Reglas_de_Negocio.md:9 | Catálogo de 30 RN; RN-13/RN-21 fuera de horizonte. |
| 08_Historias_de_Usuario.md:3,5,841,863 | Requisitos actuales/futuros, ideas fuera y anexo QA histórico; no catálogo de funcionalidades aceptadas. |
| 09_Product_Backlog.md:42,59,134 | Selección R1 de 9 HU, 65 posteriores sin Sprint, 8 ideas excluidas. |
| 14_Sprint_Planning.md:3,20-29; 16_Task_Breakdown.md:3,17-22 | Plan y desglose históricos: 67 tareas, 216 horas estimadas, sin acreditar ejecución. |
| r1-pmv/CONTROL_SPRINTS.md:3,69-94 | Declaraciones históricas de Sprints 1–3 y mejoras; marcas y cifras no se reejecutaron aquí. |
| 21_Alcance_Actual_y_Diferencias.md:3,5,23-29,42 | Guía de revisión del 5/11 y resultados de otra ejecución; punto de partida, con contradicciones pendientes. |

La fecha y vigencia del libro PLANIFICACION_SCRUM_R1PMV.xlsx se inventarían por separado en el anexo de fuentes/entorno; no se usó como autoridad ni se modificó en este índice.

## Conteos reproducibles

- HU con CA numerados: 74; CA base individuales: 219.
- Selección R1: 9 HU / 41 CA; posteriores: 65 HU; fuera: 8 ideas sin CA detallados.
- Reglas: 30. Tareas de 16: 67 (16 Tasks / 51 Subtasks). Filas CA de matriz R1: 41.
- Los 9 agregados QA de 08:869-877 se inventarían aparte, sin sumarlos a los CA base: usan etiquetas reutilizadas y agrupaciones de HU, por lo que no existe un ID de CA inequívoco por afirmación.

## HU, CA y dependencias por módulo

`R1 SELECCIONADO` describe el compromiso histórico; `PREVISTO/FUTURO` describe su posición en 09, incluso cuando CONTROL declara implementaciones posteriores. Todos los CA quedan NO EXAMINADO en esta extracción. Un adicional declarado exige contrastar código y ejecución antes de afirmar cumplimiento.

### AUTH

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-AUTH-01 — empleado de la bodega | R1 SELECCIONADO | CA-01 L18; CA-02 L19; CA-03 L20; CA-04 L21 | RN-29 / — | 08_Historias_de_Usuario.md:13; 09_Product_Backlog.md:46 |
| HU-AUTH-02 — empleado o administrador | PREVISTO/FUTURO | CA-01 L30; CA-02 L31; CA-03 L32 | RN-17 / HU-AUTH-01 | 08_Historias_de_Usuario.md:25; 09_Product_Backlog.md:75 |
| HU-AUTH-03 — empleado de la bodega | R1 SELECCIONADO | CA-01 L41; CA-02 L42; CA-03 L43 | RN-29, RN-30 / HU-AUTH-01 | 08_Historias_de_Usuario.md:36; 09_Product_Backlog.md:47 |
| HU-AUTH-04a — empleado | PREVISTO/FUTURO | CA-01 L52; CA-02 L53; CA-03 L54 | — / HU-AUTH-01, HU-AUTH-03 | 08_Historias_de_Usuario.md:47; 09_Product_Backlog.md:118 |
| HU-AUTH-04b — vendedor | PREVISTO/FUTURO | CA-01 L63; CA-02 L64 | — / HU-AUTH-04a, HU-VEN-01b | 08_Historias_de_Usuario.md:58; 09_Product_Backlog.md:119 |
| HU-AUTH-05 — empleado | PREVISTO/FUTURO | CA-01 L73; CA-02 L74; CA-03 L75; CA-04 L76; CA-05 L77 | RN-17, RN-18, RN-24 / HU-AUTH-01 | 08_Historias_de_Usuario.md:68; 09_Product_Backlog.md:120 |

### USR

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-USR-01 — administrador o dueño | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:44 | CA-01 L86; CA-02 L87; CA-03 L88 | — / HU-AUTH-01 | 08_Historias_de_Usuario.md:81; 09_Product_Backlog.md:77 |
| HU-USR-02 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:45 | CA-01 L97; CA-02 L98; CA-03 L99; CA-04 L100 | RN-12, RN-24 / HU-AUTH-01 | 08_Historias_de_Usuario.md:92; 09_Product_Backlog.md:76 |
| HU-USR-03 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:58 | CA-01 L109; CA-02 L110; CA-03 L111 | RN-12 / HU-USR-02 | 08_Historias_de_Usuario.md:104; 09_Product_Backlog.md:122 |
| HU-USR-04 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:59 | CA-01 L120; CA-02 L121; CA-03 L122 | — / HU-USR-01 | 08_Historias_de_Usuario.md:115; 09_Product_Backlog.md:78 |
| HU-USR-05 — administrador | PREVISTO/FUTURO | CA-01 L131; CA-02 L132 | — / HU-USR-04 | 08_Historias_de_Usuario.md:126; 09_Product_Backlog.md:123 |
| HU-USR-06 — administrador | PREVISTO/FUTURO | CA-01 L141; CA-02 L142 | — / HU-USR-01, HU-AUTH-01 | 08_Historias_de_Usuario.md:136; 09_Product_Backlog.md:121 |

### LOG

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-LOG-01 — administrador o dueño | PREVISTO/FUTURO | CA-01 L151; CA-02 L152; CA-03 L153 | — / HU-AUTH-01, HU-AUTH-02 | 08_Historias_de_Usuario.md:146; 09_Product_Backlog.md:124 |

### CAT

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-CAT-01 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:35 | CA-01 L166; CA-02 L167 | — / HU-AUTH-01 | 08_Historias_de_Usuario.md:161; 09_Product_Backlog.md:66 |
| HU-CAT-02 — administrador de la bodega | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:36 | CA-01 L176; CA-02 L177; CA-03 L178 | — / HU-AUTH-01 | 08_Historias_de_Usuario.md:171; 09_Product_Backlog.md:65 |
| HU-CAT-03 — administrador | PREVISTO/FUTURO | CA-01 L187; CA-02 L188 | — / HU-CAT-02 | 08_Historias_de_Usuario.md:182; 09_Product_Backlog.md:125 |
| HU-CAT-04 — administrador | PREVISTO/FUTURO | CA-01 L197; CA-02 L198 | — / HU-CAT-02, HU-PROD-01 | 08_Historias_de_Usuario.md:192; 09_Product_Backlog.md:126 |

### PROD

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-PROD-01 — administrador o vendedor | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:37 | CA-01 L207; CA-02 L208; CA-03 L209 | RN-06 / HU-PROD-02 | 08_Historias_de_Usuario.md:202; 09_Product_Backlog.md:67 |
| HU-PROD-02 — administrador de la bodega | R1 SELECCIONADO | CA-01 L218; CA-02 L219; CA-03 L220; CA-04 L221; CA-05 L222 | RN-06, RN-27, RN-29 / HU-AUTH-01 | 08_Historias_de_Usuario.md:213; 09_Product_Backlog.md:48 |
| HU-PROD-03 — administrador | PREVISTO/FUTURO | CA-01 L231; CA-02 L232 | — / HU-PROD-02 | 08_Historias_de_Usuario.md:226; 09_Product_Backlog.md:127 |
| HU-PROD-04 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:38 | CA-01 L241; CA-02 L242; CA-03 L243; CA-04 L244; CA-05 L245 | RN-06 / HU-PROD-02 | 08_Historias_de_Usuario.md:236; 09_Product_Backlog.md:68 |
| HU-PROD-05 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:39 | CA-01 L254; CA-02 L255; CA-03 L256 | — / HU-PROD-02 | 08_Historias_de_Usuario.md:249; 09_Product_Backlog.md:69 |
| HU-PROD-06 — administrador o encargado del almacén | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:40 | CA-01 L265; CA-02 L266; CA-03 L267 | RN-03 / HU-INV-01a | 08_Historias_de_Usuario.md:260; 09_Product_Backlog.md:70 |

### PROV

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-PROV-01 — administrador o encargado del almacén | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:60 | CA-01 L276; CA-02 L277 | — / HU-AUTH-01 | 08_Historias_de_Usuario.md:271; 09_Product_Backlog.md:95 |
| HU-PROV-02 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:61 | CA-01 L286; CA-02 L287; CA-03 L288 | — / HU-AUTH-01 | 08_Historias_de_Usuario.md:281; 09_Product_Backlog.md:94 |
| HU-PROV-03 — administrador | PREVISTO/FUTURO | CA-01 L297; CA-02 L298 | — / HU-PROV-02 | 08_Historias_de_Usuario.md:292; 09_Product_Backlog.md:129 |
| HU-PROV-04 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:62 | CA-01 L307; CA-02 L308; CA-03 L309 | — / HU-PROV-01 | 08_Historias_de_Usuario.md:302; 09_Product_Backlog.md:96 |

### INV

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-INV-01a — encargado del almacén | R1 SELECCIONADO | CA-01 L322; CA-02 L323; CA-03 L324; CA-04 L325; CA-05 L326 | RN-01, RN-03, RN-14, RN-19, RN-29 / HU-PROD-02 | 08_Historias_de_Usuario.md:317; 09_Product_Backlog.md:49 |
| HU-INV-01b — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:63 | CA-01 L335; CA-02 L336 | RN-14 / HU-INV-01a | 08_Historias_de_Usuario.md:330; 09_Product_Backlog.md:97 |
| HU-INV-02 — encargado del almacén | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:64 | CA-01 L345; CA-02 L346; CA-03 L347; CA-04 L348 | RN-04, RN-05, RN-20 / HU-INV-01a | 08_Historias_de_Usuario.md:340; 09_Product_Backlog.md:79 |
| HU-INV-03 — administrador | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:65 | CA-01 L357; CA-02 L358; CA-03 L359 | RN-01 / HU-INV-01a | 08_Historias_de_Usuario.md:352; 09_Product_Backlog.md:80 |
| HU-INV-04 — administrador o encargado del almacén | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:88 | CA-01 L368; CA-02 L369; CA-03 L370; CA-04 L371 | — / HU-INV-01a, HU-VEN-01c, HU-INV-02, HU-INV-03 | 08_Historias_de_Usuario.md:363; 09_Product_Backlog.md:81 |
| HU-INV-05 — administrador o dueño | PREVISTO/FUTURO | CA-01 L380; CA-02 L381 | — / HU-INV-02 | 08_Historias_de_Usuario.md:375; 09_Product_Backlog.md:82 |
| HU-INV-06 — administrador o dueño | PREVISTO/FUTURO | CA-01 L390; CA-02 L391 | — / HU-INV-03 | 08_Historias_de_Usuario.md:385; 09_Product_Backlog.md:83 |

### SOL

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-SOL-01 — encargado del almacén | PREVISTO/FUTURO | CA-01 L400; CA-02 L401; CA-03 L402 | RN-06 / HU-PROD-02, HU-PROV-02 | 08_Historias_de_Usuario.md:395; 09_Product_Backlog.md:98 |
| HU-SOL-02 — encargado del almacén o administrador | PREVISTO/FUTURO | CA-01 L411; CA-02 L412; CA-03 L413 | — / HU-SOL-01 | 08_Historias_de_Usuario.md:406; 09_Product_Backlog.md:99 |
| HU-SOL-03 — administrador o dueño | PREVISTO/FUTURO | CA-01 L422; CA-02 L423; CA-03 L424 | RN-16 / HU-SOL-01 | 08_Historias_de_Usuario.md:417; 09_Product_Backlog.md:100 |
| HU-SOL-04 — administrador o dueño | PREVISTO/FUTURO | CA-01 L433; CA-02 L434 | — / HU-SOL-01 | 08_Historias_de_Usuario.md:428; 09_Product_Backlog.md:101 |
| HU-SOL-05a — encargado del almacén | PREVISTO/FUTURO | CA-01 L443; CA-02 L444; CA-03 L445; CA-04 L446 | RN-01, RN-03, RN-14, RN-19 / HU-SOL-03, HU-INV-01a, HU-INV-01b | 08_Historias_de_Usuario.md:438; 09_Product_Backlog.md:102 |
| HU-SOL-05b — encargado del almacén | PREVISTO/FUTURO | CA-01 L455; CA-02 L456; CA-03 L457 | RN-01, RN-03, RN-14, RN-19 / HU-SOL-05a | 08_Historias_de_Usuario.md:450; 09_Product_Backlog.md:103 |

### CAJA

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-CAJA-01 — vendedor | R1 SELECCIONADO | CA-01 L470; CA-02 L471; CA-03 L472; CA-04 L473 | RN-10, RN-29 / HU-AUTH-01 | 08_Historias_de_Usuario.md:465; 09_Product_Backlog.md:50 |
| HU-CAJA-02 — vendedor | R1 SELECCIONADO | CA-01 L482; CA-02 L483; CA-03 L484; CA-04 L485; CA-05 L486 | RN-10, RN-29, RN-30 / HU-CAJA-01, HU-VEN-01c | 08_Historias_de_Usuario.md:477; 09_Product_Backlog.md:54 |
| HU-CAJA-03 — vendedor | PREVISTO/FUTURO | CA-01 L495; CA-02 L496; CA-03 L497; CA-04 L498 | RN-10, RN-11, RN-15 / HU-CAJA-01 | 08_Historias_de_Usuario.md:490; 09_Product_Backlog.md:88 |
| HU-CAJA-04 — vendedor | PREVISTO/FUTURO | CA-01 L507; CA-02 L508 | — / HU-CAJA-01, HU-VEN-01c, HU-CAJA-03 | 08_Historias_de_Usuario.md:502; 09_Product_Backlog.md:89 |
| HU-CAJA-05 — administrador o dueño | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:43 | CA-01 L517; CA-02 L518 | — / HU-CAJA-02 | 08_Historias_de_Usuario.md:512; 09_Product_Backlog.md:73 |
| HU-CAJA-06 — administrador o dueño | PREVISTO/FUTURO | CA-01 L527; CA-02 L528 | — / HU-CAJA-02 | 08_Historias_de_Usuario.md:522; 09_Product_Backlog.md:90 |
| HU-CAJA-07 — administrador | PREVISTO/FUTURO | CA-01 L537; CA-02 L538 | RN-23 / HU-CAJA-01 | 08_Historias_de_Usuario.md:532; 09_Product_Backlog.md:91 |

### VEN

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-VEN-01a — vendedor | PREVISTO/FUTURO | CA-01 L547; CA-02 L548; CA-03 L549 | RN-22 / HU-CAJA-01 | 08_Historias_de_Usuario.md:542; 09_Product_Backlog.md:74 |
| HU-VEN-01b — vendedor | R1 SELECCIONADO | CA-01 L558; CA-02 L559; CA-03 L560; CA-04 L561; CA-05 L562 | RN-03, RN-10, RN-27, RN-29, RN-30 / HU-CAJA-01, HU-INV-01a | 08_Historias_de_Usuario.md:553; 09_Product_Backlog.md:51 |
| HU-VEN-01c — vendedor | R1 SELECCIONADO | CA-01 L571; CA-02 L572; CA-03 L573; CA-04 L574; CA-05 L575; CA-06 L576 | RN-03, RN-10, RN-19, RN-25, RN-27, RN-28, RN-29, RN-30 / HU-VEN-01b | 08_Historias_de_Usuario.md:566; 09_Product_Backlog.md:52 |
| HU-VEN-02a — vendedor | R1 SELECCIONADO | CA-01 L585; CA-02 L586; CA-03 L587; CA-04 L588 | RN-26, RN-27, RN-29 / HU-VEN-01c | 08_Historias_de_Usuario.md:580; 09_Product_Backlog.md:53 |
| HU-VEN-04 — vendedor | PREVISTO/FUTURO | CA-01 L597; CA-02 L598 | — / HU-VEN-01b | 08_Historias_de_Usuario.md:592; 09_Product_Backlog.md:128 |
| HU-VEN-05a — vendedor | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:41 | CA-01 L607; CA-02 L608 | RN-07 / HU-VEN-01c, HU-CAJA-01 | 08_Historias_de_Usuario.md:602; 09_Product_Backlog.md:71 |
| HU-VEN-05b — administrador o dueño | PREVISTO/FUTURO; adicional declarado en r1-pmv/CONTROL_SPRINTS.md:42 | CA-01 L617; CA-02 L618; CA-03 L619 | RN-07 / HU-VEN-01c | 08_Historias_de_Usuario.md:612; 09_Product_Backlog.md:72 |
| HU-VEN-06a — administrador o dueño | PREVISTO/FUTURO | CA-01 L628; CA-02 L629; CA-03 L630 | RN-08, RN-10 / HU-VEN-01c, HU-VEN-02a | 08_Historias_de_Usuario.md:623; 09_Product_Backlog.md:84 |
| HU-VEN-06b — administrador o dueño | PREVISTO/FUTURO | CA-01 L639; CA-02 L640 | RN-08 / HU-VEN-06a, HU-VEN-07 | 08_Historias_de_Usuario.md:634; 09_Product_Backlog.md:87 |
| HU-VEN-06c — encargado del almacén o administrador | PREVISTO/FUTURO | CA-01 L649; CA-02 L650; CA-03 L651 | RN-09 / HU-VEN-06a, HU-INV-02 | 08_Historias_de_Usuario.md:644; 09_Product_Backlog.md:85 |
| HU-VEN-07 — vendedor | PREVISTO/FUTURO | CA-01 L660; CA-02 L661; CA-03 L662; CA-04 L663; CA-05 L664; CA-06 L665 | RN-02 / HU-VEN-01b, HU-VEN-01c | 08_Historias_de_Usuario.md:655; 09_Product_Backlog.md:86 |
| HU-VEN-02b — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:143 |
| HU-VEN-02c — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:144 |
| HU-VEN-03 — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:145 |
| HU-VEN-08 — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:146 |
| HU-VEN-09 — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:147 |

### CONF

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-CONF-01 — administrador o dueño | PREVISTO/FUTURO | CA-01 L678; CA-02 L679 | — / HU-AUTH-01 | 08_Historias_de_Usuario.md:673; 09_Product_Backlog.md:92 |
| HU-CONF-02 — administrador | PREVISTO/FUTURO | CA-01 L688; CA-02 L689; CA-03 L690 | — / HU-CONF-01 | 08_Historias_de_Usuario.md:683; 09_Product_Backlog.md:93 |

### DASH

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-DASH-01 — dueño o administrador | PREVISTO/FUTURO | CA-01 L699; CA-02 L700; CA-03 L701 | — / HU-VEN-01c | 08_Historias_de_Usuario.md:694; 09_Product_Backlog.md:106 |
| HU-DASH-02 — dueño o administrador | PREVISTO/FUTURO | CA-01 L710; CA-02 L711 | — / HU-VEN-01c | 08_Historias_de_Usuario.md:705; 09_Product_Backlog.md:113 |
| HU-DASH-03 — dueño o administrador | PREVISTO/FUTURO | CA-01 L720; CA-02 L721; CA-03 L722 | RN-06, RN-23 / HU-INV-01a, HU-CAJA-05, HU-PROD-06 | 08_Historias_de_Usuario.md:715; 09_Product_Backlog.md:105 |
| HU-DASH-04 — dueño o administrador | PREVISTO/FUTURO | CA-01 L731; CA-02 L732 | — / HU-VEN-01c | 08_Historias_de_Usuario.md:726; 09_Product_Backlog.md:114 |
| HU-DASH-05 — dueño o administrador | PREVISTO/FUTURO | CA-01 L741; CA-02 L742; CA-03 L743 | — / HU-SOL-01 | 08_Historias_de_Usuario.md:736; 09_Product_Backlog.md:115 |

### REP

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-REP-01 — dueño o administrador | PREVISTO/FUTURO | CA-01 L752; CA-02 L753 | — / HU-VEN-01c | 08_Historias_de_Usuario.md:747; 09_Product_Backlog.md:107 |
| HU-REP-02 — dueño de la bodega | PREVISTO/FUTURO | CA-01 L762; CA-02 L763; CA-03 L764 | — / HU-VEN-01c | 08_Historias_de_Usuario.md:757; 09_Product_Backlog.md:108 |
| HU-REP-03 — dueño o administrador | PREVISTO/FUTURO | CA-01 L773; CA-02 L774 | — / HU-VEN-01c | 08_Historias_de_Usuario.md:768; 09_Product_Backlog.md:116 |
| HU-REP-04 — dueño o administrador | PREVISTO/FUTURO | CA-01 L783; CA-02 L784 | — / HU-VEN-01c, HU-VEN-07 | 08_Historias_de_Usuario.md:778; 09_Product_Backlog.md:109 |
| HU-REP-05 — administrador o dueño | PREVISTO/FUTURO | CA-01 L793; CA-02 L794; CA-03 L795 | RN-06 / HU-INV-01a | 08_Historias_de_Usuario.md:788; 09_Product_Backlog.md:104 |
| HU-REP-06 — dueño o administrador | PREVISTO/FUTURO | CA-01 L804; CA-02 L805 | — / HU-INV-01a | 08_Historias_de_Usuario.md:799; 09_Product_Backlog.md:110 |
| HU-REP-07 — dueño de la bodega | PREVISTO/FUTURO | CA-01 L814; CA-02 L815; CA-03 L816 | RN-14, RN-27, RN-28 / HU-VEN-01c, HU-INV-01a | 08_Historias_de_Usuario.md:809; 09_Product_Backlog.md:111 |
| HU-REP-08 — dueño o administrador | PREVISTO/FUTURO | CA-01 L825; CA-02 L826 | — / HU-INV-02 | 08_Historias_de_Usuario.md:820; 09_Product_Backlog.md:112 |
| HU-REP-09 — dueño o administrador | PREVISTO/FUTURO | CA-01 L836; CA-02 L837 | — / HU-REP-01, HU-REP-02, HU-REP-05, HU-REP-07, HU-REP-08 | 08_Historias_de_Usuario.md:830; 09_Product_Backlog.md:117 |

### CLI

| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |
|---|---|---|---|---|
| HU-CLI-01 — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:140 |
| HU-CLI-02 — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:141 |
| HU-CLI-03 — No detallado | FUERA DEL HORIZONTE | Sin CA detallados | — / — | 08_Historias_de_Usuario.md:843; 09_Product_Backlog.md:142 |

## Reglas e identificadores relacionados

| RN | Nombre | HU declaradas en regla | Fuente / estado |
|---|---|---|---|
| RN-01 | Control de existencias | HU-INV-01a, HU-INV-03, HU-SOL-05a, HU-SOL-05b | 07_Reglas_de_Negocio.md:13 / NO EXAMINADO |
| RN-02 | Pagos con billetera digital | HU-VEN-07 | 07_Reglas_de_Negocio.md:14 / NO EXAMINADO |
| RN-03 | Control de vencimientos | HU-INV-01a, HU-VEN-01b, HU-VEN-01c, HU-PROD-06, HU-SOL-05a, HU-SOL-05b | 07_Reglas_de_Negocio.md:15 / NO EXAMINADO |
| RN-04 | Mermas y pérdidas | HU-INV-02 | 07_Reglas_de_Negocio.md:16 / NO EXAMINADO |
| RN-05 | Causas de baja | HU-INV-02 | 07_Reglas_de_Negocio.md:17 / NO EXAMINADO |
| RN-06 | Umbral de existencias mínimas | HU-PROD-01, HU-PROD-02, HU-PROD-04, HU-SOL-01, HU-REP-05, HU-DASH-03 | 07_Reglas_de_Negocio.md:18 / NO EXAMINADO |
| RN-07 | Acceso a ventas | HU-VEN-05a, HU-VEN-05b | 07_Reglas_de_Negocio.md:19 / NO EXAMINADO |
| RN-08 | Anulación de ventas | HU-VEN-06a, HU-VEN-06b | 07_Reglas_de_Negocio.md:20 / NO EXAMINADO |
| RN-09 | Destino de mercadería | HU-VEN-06c | 07_Reglas_de_Negocio.md:21 / NO EXAMINADO |
| RN-10 | Turno y efectivo de caja | HU-CAJA-01, HU-CAJA-02, HU-CAJA-03, HU-VEN-01b, HU-VEN-01c, HU-VEN-06a | 07_Reglas_de_Negocio.md:22 / NO EXAMINADO |
| RN-11 | Movimientos de caja | HU-CAJA-03 | 07_Reglas_de_Negocio.md:23 / NO EXAMINADO |
| RN-12 | Cuentas de empleados | HU-USR-02, HU-USR-03 | 07_Reglas_de_Negocio.md:24 / NO EXAMINADO |
| RN-13 | Comprobantes futuros | — | 07_Reglas_de_Negocio.md:25 / FUERA DEL HORIZONTE |
| RN-14 | Costo de mercadería | HU-INV-01a, HU-INV-01b, HU-SOL-05a, HU-SOL-05b, HU-REP-07 | 07_Reglas_de_Negocio.md:26 / NO EXAMINADO |
| RN-15 | Moneda en caja | HU-CAJA-03 | 07_Reglas_de_Negocio.md:27 / NO EXAMINADO |
| RN-16 | Reposición | HU-SOL-03 | 07_Reglas_de_Negocio.md:28 / NO EXAMINADO |
| RN-17 | Seguridad de acceso | HU-AUTH-02, HU-AUTH-05 | 07_Reglas_de_Negocio.md:29 / NO EXAMINADO |
| RN-18 | Recuperación de clave | HU-AUTH-05 | 07_Reglas_de_Negocio.md:30 / NO EXAMINADO |
| RN-19 | Prioridad de salida | HU-INV-01a, HU-VEN-01c, HU-SOL-05a, HU-SOL-05b | 07_Reglas_de_Negocio.md:31 / NO EXAMINADO |
| RN-20 | Detalle de pérdidas | HU-INV-02 | 07_Reglas_de_Negocio.md:32 / NO EXAMINADO |
| RN-21 | Identificación tributaria futura | — | 07_Reglas_de_Negocio.md:33 / FUERA DEL HORIZONTE |
| RN-22 | Seguridad en mostrador | HU-VEN-01a | 07_Reglas_de_Negocio.md:34 / NO EXAMINADO |
| RN-23 | Inactividad de caja | HU-CAJA-07, HU-DASH-03 | 07_Reglas_de_Negocio.md:35 / NO EXAMINADO |
| RN-24 | Seguridad de contraseñas | HU-USR-02, HU-AUTH-05 | 07_Reglas_de_Negocio.md:36 / NO EXAMINADO |
| RN-25 | Registro de venta | HU-VEN-01c | 07_Reglas_de_Negocio.md:37 / NO EXAMINADO |
| RN-26 | Constancia interna | HU-VEN-02a | 07_Reglas_de_Negocio.md:38 / NO EXAMINADO |
| RN-27 | Cálculo de IGV | HU-PROD-02, HU-VEN-01b, HU-VEN-01c, HU-VEN-02a, HU-REP-07 | 07_Reglas_de_Negocio.md:39 / NO EXAMINADO |
| RN-28 | Costo histórico de venta | HU-VEN-01c, HU-REP-07 | 07_Reglas_de_Negocio.md:40 / NO EXAMINADO |
| RN-29 | Autorización de R1-PMV | HU-AUTH-01, HU-AUTH-03, HU-PROD-02, HU-INV-01a, HU-CAJA-01, HU-VEN-01b, HU-VEN-01c, HU-VEN-02a, HU-CAJA-02 | 07_Reglas_de_Negocio.md:41 / NO EXAMINADO |
| RN-30 | Venta en preparación | HU-AUTH-03, HU-VEN-01b, HU-VEN-01c, HU-CAJA-02 | 07_Reglas_de_Negocio.md:42 / NO EXAMINADO |

## Tareas técnicas: identidad, pertenencia y dependencias

Estado de todas estas filas: PLAN HISTÓRICO / NO EXAMINADO. No son HU ni prueba de trabajo realizado. [H] y [I] conservan el significado de 16:35-36; su referencia no reactiva Jira.

| ID | Tipo / padre | CA/RN/NFR declarados | Dependencias | Fuente |
|---|---|---|---|---|
| S1-ARQ-01 | Task / TRANSVERSAL | DoR; DT-01 a DT-15 | Ninguna | 16_Task_Breakdown.md:57 |
| S1-PLAT-01 | Task / TRANSVERSAL | DoD-5,8 | Ninguna | 16_Task_Breakdown.md:58 |
| S1-CI-01 | Task / TRANSVERSAL | DoD-5,6,8 | [H] S1-PLAT-01 | 16_Task_Breakdown.md:59 |
| S1-DB-01 | Task / TRANSVERSAL | RN-01, RN-03, RN-10, RN-12, RN-14, RN-19, RN-25, RN-26, RN-27, RN-28, RN-29 | [H] S1-ARQ-01 | 16_Task_Breakdown.md:60 |
| S1-DB-02 | Task / TRANSVERSAL | DoD-3; NFR-01, NFR-02, NFR-08 | [H] S1-DB-01 | 16_Task_Breakdown.md:61 |
| S1-DB-03 | Task / TRANSVERSAL | DoD-3; RN-10, RN-12, RN-25, RN-26 | [H] S1-DB-02 | 16_Task_Breakdown.md:62 |
| S1-DB-04 | Task / TRANSVERSAL | HU-AUTH-01; HU-PROD-02; HU-CAJA-01 | [H] S1-DB-02; [I] S1-SEC-02 | 16_Task_Breakdown.md:63 |
| S1-DB-05 | Task / TRANSVERSAL | DoD-6,7; NFR-05 | [H] S1-DB-04 | 16_Task_Breakdown.md:64 |
| S1-SEC-01 | Task / TRANSVERSAL | DoD-5; NFR-08, NFR-09 | [H] S1-ARQ-01 | 16_Task_Breakdown.md:65 |
| S1-SEC-02 | Task / TRANSVERSAL | DoD-5; HU-AUTH-01, HU-AUTH-03; RN-29; NFR-03, NFR-09 | [H] S1-SEC-01 | 16_Task_Breakdown.md:66 |
| S1-ENV-01 | Task / TRANSVERSAL | Puerta de piloto; NFR-06, NFR-07, NFR-08, NFR-09 | [H] S1-PLAT-01, S1-DB-02, S1-SEC-01; [I] S1-CI-01 | 16_Task_Breakdown.md:67 |
| S1-QA-DB-01 | Task / TRANSVERSAL | DoD-3,6 | [H] S1-DB-03, S1-DB-04, S1-DB-05, S1-CI-01 | 16_Task_Breakdown.md:68 |
| S1-QA-DB-02 | Task / TRANSVERSAL | DoD-4; RN-25 | [H] S1-INV01A-TXDB, S1-VEN01C-TXDB, S1-CAJA02-SVC | 16_Task_Breakdown.md:69 |
| S1-QA-DB-03 | Task / TRANSVERSAL | RN-01, RN-10, RN-19, RN-25, RN-26 | [H] S1-CAJA01-CONC, S1-VEN01C-IDEM, S1-CAJA02-SVC; [I] S1-INV01A-TXDB | 16_Task_Breakdown.md:70 |
| S1-OPS-DB-01 | Task / TRANSVERSAL | Puerta de piloto; NFR-10 | [H] S1-ENV-01, S1-DB-05 | 16_Task_Breakdown.md:71 |
| S1-OPS-DB-02 | Task / TRANSVERSAL | Puerta de piloto; NFR-10 | [H] S1-OPS-DB-01, S1-QA-DB-01; [I] nueve Stories integradas | 16_Task_Breakdown.md:72 |
| S1-AUTH01-UI | Subtask / UI / HU-AUTH-01 | CA1-4; NFR-06 | [H] S1-ARQ-01, S1-PLAT-01; [I] S1-AUTH01-SVC | 16_Task_Breakdown.md:81 |
| S1-AUTH01-SVC | Subtask / servicio-BD / HU-AUTH-01 | CA1-3; RN-12; NFR-03, NFR-09 | [H] S1-DB-02, S1-SEC-02; [I] S1-DB-04 | 16_Task_Breakdown.md:82 |
| S1-AUTH01-AUTHZ | Subtask / seguridad / HU-AUTH-01 | CA1,4; RN-29; NFR-03 | [H] S1-AUTH01-SVC, S1-SEC-02 | 16_Task_Breakdown.md:83 |
| S1-AUTH01-AUTO | Subtask / QA automática / HU-AUTH-01 | CA1-4 | [H] S1-AUTH01-SVC, S1-AUTH01-AUTHZ, S1-CI-01 | 16_Task_Breakdown.md:84 |
| S1-AUTH01-MAN | Subtask / QA manual / HU-AUTH-01 | CA1-4 | [H] S1-AUTH01-UI, S1-AUTH01-AUTO | 16_Task_Breakdown.md:85 |
| S1-AUTH01-REV | Subtask / revisión independiente / HU-AUTH-01 | CA1-4; DoD | [H] S1-AUTH01-MAN | 16_Task_Breakdown.md:86 |
| S1-AUTH03-UI | Subtask / UI / HU-AUTH-03 | CA1-3; RN-30 | [H] S1-AUTH01-UI; [I] S1-AUTH03-SVC | 16_Task_Breakdown.md:93 |
| S1-AUTH03-SVC | Subtask / servicio-seguridad / HU-AUTH-03 | CA1-3; RN-29, RN-30; NFR-03, NFR-09 | [H] S1-AUTH01-SVC, S1-AUTH01-AUTHZ | 16_Task_Breakdown.md:94 |
| S1-AUTH03-AUTO | Subtask / QA automática / HU-AUTH-03 | CA1-3 | [H] S1-AUTH03-UI, S1-AUTH03-SVC, S1-CI-01 | 16_Task_Breakdown.md:95 |
| S1-AUTH03-MAN | Subtask / QA manual / HU-AUTH-03 | CA1-3 | [H] S1-AUTH03-AUTO | 16_Task_Breakdown.md:96 |
| S1-AUTH03-REV | Subtask / revisión independiente / HU-AUTH-03 | CA1-3; DoD | [H] S1-AUTH03-MAN | 16_Task_Breakdown.md:97 |
| S1-PROD02-UI | Subtask / UI / HU-PROD-02 | CA1-5; RN-06, RN-27 | [H] S1-ARQ-01; [I] S1-PROD02-SVC | 16_Task_Breakdown.md:104 |
| S1-PROD02-SVC | Subtask / servicio-BD / HU-PROD-02 | CA1-5; RN-06, RN-27, RN-29 | [H] S1-DB-03; [I] S1-AUTH01-AUTHZ | 16_Task_Breakdown.md:105 |
| S1-PROD02-AUTO | Subtask / QA automática / HU-PROD-02 | CA1-5 | [H] S1-PROD02-SVC, S1-CI-01 | 16_Task_Breakdown.md:106 |
| S1-PROD02-MAN | Subtask / QA manual / HU-PROD-02 | CA1-5 | [H] S1-PROD02-UI, S1-PROD02-AUTO; [I] S1-DB-04 | 16_Task_Breakdown.md:107 |
| S1-PROD02-REV | Subtask / revisión independiente / HU-PROD-02 | CA1-5; DoD | [H] S1-PROD02-MAN | 16_Task_Breakdown.md:108 |
| S1-INV01A-UI | Subtask / UI / HU-INV-01a | CA1-5 | [H] S1-ARQ-01; [I] S1-PROD02-UI, S1-INV01A-VALID | 16_Task_Breakdown.md:115 |
| S1-INV01A-VALID | Subtask / servicio / HU-INV-01a | CA1-3; RN-01, RN-03, RN-29; NFR-03 | [H] S1-DB-03; [I] S1-PROD02-SVC, S1-AUTH01-AUTHZ | 16_Task_Breakdown.md:116 |
| S1-INV01A-TXDB | Subtask / servicio-BD / HU-INV-01a | CA1-5; RN-01, RN-14, RN-19 | [H] S1-DB-03, S1-INV01A-VALID; [I] S1-PROD02-SVC | 16_Task_Breakdown.md:117 |
| S1-INV01A-AUTO | Subtask / QA automática / HU-INV-01a | CA1-5 | [H] S1-INV01A-TXDB, S1-CI-01 | 16_Task_Breakdown.md:118 |
| S1-INV01A-MAN | Subtask / QA manual / HU-INV-01a | CA1-5 | [H] S1-INV01A-UI, S1-INV01A-AUTO | 16_Task_Breakdown.md:119 |
| S1-INV01A-REV | Subtask / revisión independiente / HU-INV-01a | CA1-5; DoD | [H] S1-INV01A-MAN; [I] S1-QA-DB-02 | 16_Task_Breakdown.md:120 |
| S1-CAJA01-UI | Subtask / UI / HU-CAJA-01 | CA1-4; RN-10, RN-29 | [H] S1-ARQ-01; [I] S1-CAJA01-SVC | 16_Task_Breakdown.md:127 |
| S1-CAJA01-SVC | Subtask / servicio-BD / HU-CAJA-01 | CA1,2,4; RN-10, RN-29 | [H] S1-DB-03; [I] S1-AUTH01-AUTHZ | 16_Task_Breakdown.md:128 |
| S1-CAJA01-CONC | Subtask / BD-concurrencia / HU-CAJA-01 | CA3; RN-10 | [H] S1-CAJA01-SVC | 16_Task_Breakdown.md:129 |
| S1-CAJA01-AUTO | Subtask / QA automática / HU-CAJA-01 | CA1-4 | [H] S1-CAJA01-CONC, S1-CI-01 | 16_Task_Breakdown.md:130 |
| S1-CAJA01-MAN | Subtask / QA manual / HU-CAJA-01 | CA1-4 | [H] S1-CAJA01-UI, S1-CAJA01-AUTO | 16_Task_Breakdown.md:131 |
| S1-CAJA01-REV | Subtask / revisión independiente / HU-CAJA-01 | CA1-4; DoD | [H] S1-CAJA01-MAN | 16_Task_Breakdown.md:132 |
| S1-VEN01B-UI | Subtask / UI / HU-VEN-01b | CA2,3,5; RN-27, RN-30 | [H] S1-ARQ-01; [I] S1-PROD02-UI, S1-VEN01B-SVC | 16_Task_Breakdown.md:139 |
| S1-VEN01B-SVC | Subtask / servicio-BD / HU-VEN-01b | CA1-5; RN-03, RN-27, RN-29, RN-30 | [H] S1-DB-03; [I] S1-AUTH01-AUTHZ, S1-INV01A-TXDB, S1-CAJA01-SVC | 16_Task_Breakdown.md:140 |
| S1-VEN01B-AUTO | Subtask / QA automática / HU-VEN-01b | CA1-5; NFR-05 | [H] S1-VEN01B-SVC, S1-CI-01; [I] S1-ENV-01 | 16_Task_Breakdown.md:141 |
| S1-VEN01B-MAN | Subtask / QA manual / HU-VEN-01b | CA1-5 | [H] S1-VEN01B-UI, S1-VEN01B-AUTO; [I] HU-INV-01a y HU-CAJA-01 integradas | 16_Task_Breakdown.md:142 |
| S1-VEN01B-REV | Subtask / revisión independiente / HU-VEN-01b | CA1-5; DoD | [H] S1-VEN01B-MAN | 16_Task_Breakdown.md:143 |
| S1-VEN01C-UI | Subtask / UI / HU-VEN-01c | CA1,2,5 | [H] S1-VEN01B-UI; [I] S1-VEN01C-PAY | 16_Task_Breakdown.md:150 |
| S1-VEN01C-PAY | Subtask / servicio / HU-VEN-01c | CA1,2,3; RN-25, RN-27, RN-29, RN-30; NFR-03 | [H] S1-DB-03; [I] S1-VEN01B-SVC, S1-CAJA01-SVC, S1-AUTH01-AUTHZ | 16_Task_Breakdown.md:151 |
| S1-VEN01C-FEFO | Subtask / servicio-BD / HU-VEN-01c | CA3; RN-03, RN-19 | [H] S1-DB-03; [I] S1-INV01A-TXDB | 16_Task_Breakdown.md:152 |
| S1-VEN01C-TXDB | Subtask / servicio-BD / HU-VEN-01c | CA3,4,6; RN-25, RN-28 | [H] S1-DB-03; [I] S1-VEN01C-PAY, S1-VEN01C-FEFO | 16_Task_Breakdown.md:153 |
| S1-VEN01C-IDEM | Subtask / servicio-BD / HU-VEN-01c | CA4,5; RN-25, RN-26 | [H] S1-VEN01C-TXDB | 16_Task_Breakdown.md:154 |
| S1-VEN01C-AUTO | Subtask / QA automática / HU-VEN-01c | CA1-6; NFR-05 | [H] S1-VEN01C-PAY, S1-VEN01C-FEFO, S1-VEN01C-TXDB, S1-VEN01C-IDEM, S1-CI-01; [I] S1-ENV-01 | 16_Task_Breakdown.md:155 |
| S1-VEN01C-MAN | Subtask / QA manual / HU-VEN-01c | CA1-6 | [H] S1-VEN01C-UI, S1-VEN01C-AUTO; [I] S1-QA-DB-03, HU-VEN-01b integrada | 16_Task_Breakdown.md:156 |
| S1-VEN01C-REV | Subtask / revisión independiente / HU-VEN-01c | CA1-6; DoD | [H] S1-VEN01C-MAN; [I] S1-QA-DB-02 | 16_Task_Breakdown.md:157 |
| S1-VEN02A-UI | Subtask / UI / HU-VEN-02a | CA1-3; RN-26, RN-27 | [H] S1-ARQ-01; [I] S1-VEN02A-SVC | 16_Task_Breakdown.md:164 |
| S1-VEN02A-SVC | Subtask / servicio-BD / HU-VEN-02a | CA1,2,4; RN-26, RN-27, RN-28 | [H] S1-DB-03; [I] S1-VEN01C-TXDB, S1-VEN01C-IDEM | 16_Task_Breakdown.md:165 |
| S1-VEN02A-AUTO | Subtask / QA automática / HU-VEN-02a | CA1-4 | [H] S1-VEN02A-UI, S1-VEN02A-SVC, S1-CI-01 | 16_Task_Breakdown.md:166 |
| S1-VEN02A-MAN | Subtask / QA manual / HU-VEN-02a | CA1-4 | [H] S1-VEN02A-AUTO; [I] HU-VEN-01c integrada | 16_Task_Breakdown.md:167 |
| S1-VEN02A-REV | Subtask / revisión independiente / HU-VEN-02a | CA1-4; DoD | [H] S1-VEN02A-MAN | 16_Task_Breakdown.md:168 |
| S1-CAJA02-UI | Subtask / UI / HU-CAJA-02 | CA1-4; RN-10, RN-30 | [H] S1-CAJA01-UI; [I] S1-CAJA02-SVC | 16_Task_Breakdown.md:175 |
| S1-CAJA02-SVC | Subtask / servicio-BD / HU-CAJA-02 | CA1-5; RN-10, RN-25, RN-29, RN-30; NFR-03 | [H] S1-DB-03; [I] S1-CAJA01-CONC, S1-VEN01C-TXDB, S1-AUTH01-AUTHZ | 16_Task_Breakdown.md:176 |
| S1-CAJA02-AUTO | Subtask / QA automática / HU-CAJA-02 | CA1-5 | [H] S1-CAJA02-SVC, S1-CI-01 | 16_Task_Breakdown.md:177 |
| S1-CAJA02-MAN | Subtask / QA manual / HU-CAJA-02 | CA1-5 | [H] S1-CAJA02-UI, S1-CAJA02-AUTO; [I] S1-QA-DB-03, HU-VEN-01c integrada | 16_Task_Breakdown.md:178 |
| S1-CAJA02-REV | Subtask / revisión independiente / HU-CAJA-02 | CA1-5; DoD | [H] S1-CAJA02-MAN; [I] S1-QA-DB-02 | 16_Task_Breakdown.md:179 |

## Casos planificados de R1: índice de cobertura histórica

El inventario de pruebas reales del código se mantiene separado. AT/ST/CT/MT/PT aquí son nombres del plan; no se infiere que existan, se ejecutaran o aprobaran. La relación original puede contener errores semánticos.

| CA base | Pruebas planificadas | Fuente | Estado nuevo |
|---|---|---|---|
| HU-AUTH-01/CA-01 | AT-AUTH01-01, MT-AUTH01-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:60 | NO EJECUTADO |
| HU-AUTH-01/CA-02 | AT-AUTH01-02, ST-AUTH01-01, MT-AUTH01-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:61 | NO EJECUTADO |
| HU-AUTH-01/CA-03 | AT-AUTH01-03, ST-AUTH01-02, MT-AUTH01-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:62 | NO EJECUTADO |
| HU-AUTH-01/CA-04 | AT-AUTH01-04, ST-AUTH01-03, MT-AUTH01-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:63 | NO EJECUTADO |
| HU-AUTH-03/CA-01 | AT-AUTH03-01, MT-AUTH03-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:69 | NO EJECUTADO |
| HU-AUTH-03/CA-02 | AT-AUTH03-02, MT-AUTH03-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:70 | NO EJECUTADO |
| HU-AUTH-03/CA-03 | ST-AUTH03-01, MT-AUTH03-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:71 | NO EJECUTADO |
| HU-PROD-02/CA-01 | AT-PROD02-01, MT-PROD02-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:77 | NO EJECUTADO |
| HU-PROD-02/CA-02 | AT-PROD02-02, MT-PROD02-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:78 | NO EJECUTADO |
| HU-PROD-02/CA-03 | AT-PROD02-03, CT-PROD02-01, MT-PROD02-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:79 | NO EJECUTADO |
| HU-PROD-02/CA-04 | AT-PROD02-04, MT-PROD02-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:80 | NO EJECUTADO |
| HU-PROD-02/CA-05 | AT-PROD02-05, ST-PROD02-01, MT-PROD02-05 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:81 | NO EJECUTADO |
| HU-INV-01a/CA-01 | AT-INV01A-01, ST-INV01A-01, CT-CONC-01, MT-INV01A-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:87 | NO EJECUTADO |
| HU-INV-01a/CA-02 | AT-INV01A-02, AT-TIME-01, MT-INV01A-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:88 | NO EJECUTADO |
| HU-INV-01a/CA-03 | AT-INV01A-03, CT-ROLLBACK-01, MT-INV01A-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:89 | NO EJECUTADO |
| HU-INV-01a/CA-04 | AT-INV01A-04, MT-INV01A-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:90 | NO EJECUTADO |
| HU-INV-01a/CA-05 | AT-INV01A-05, MT-INV01A-05 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:91 | NO EJECUTADO |
| HU-CAJA-01/CA-01 | AT-CAJA01-01, ST-CAJA01-01, MT-CAJA01-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:97 | NO EJECUTADO |
| HU-CAJA-01/CA-02 | AT-CAJA01-02, MT-CAJA01-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:98 | NO EJECUTADO |
| HU-CAJA-01/CA-03 | CT-CONC-02, MT-CAJA01-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:99 | NO EJECUTADO |
| HU-CAJA-01/CA-04 | AT-CAJA01-03, ST-CAJA01-01, MT-CAJA01-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:100 | NO EJECUTADO |
| HU-VEN-01b/CA-01 | AT-VEN01B-01, ST-VEN01B-01, MT-VEN01B-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:106 | NO EJECUTADO |
| HU-VEN-01b/CA-02 | AT-VEN01B-02, MT-VEN01B-02, PT-SEARCH-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:107 | NO EJECUTADO |
| HU-VEN-01b/CA-03 | AT-VEN01B-03, MT-VEN01B-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:108 | NO EJECUTADO |
| HU-VEN-01b/CA-04 | AT-VEN01B-04, AT-TIME-02, MT-VEN01B-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:109 | NO EJECUTADO |
| HU-VEN-01b/CA-05 | AT-VEN01B-05, MT-VEN01B-05, AT-CAJA02-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:110 | NO EJECUTADO |
| HU-VEN-01c/CA-01 | AT-VEN01C-01, MT-VEN01C-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:116 | NO EJECUTADO |
| HU-VEN-01c/CA-02 | AT-VEN01C-02, MT-VEN01C-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:117 | NO EJECUTADO |
| HU-VEN-01c/CA-03 | AT-VEN01C-03, ST-VEN01C-01, CT-CONC-03, MT-VEN01C-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:118 | NO EJECUTADO |
| HU-VEN-01c/CA-04 | CT-ROLLBACK-02, PT-CHECKOUT-01, MT-VEN01C-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:119 | NO EJECUTADO |
| HU-VEN-01c/CA-05 | AT-VEN01C-04, CT-CONC-04, MT-VEN01C-05 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:120 | NO EJECUTADO |
| HU-VEN-01c/CA-06 | AT-VEN01C-05, MT-VEN01C-06 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:121 | NO EJECUTADO |
| HU-VEN-02a/CA-01 | AT-VEN02A-01, MT-VEN02A-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:127 | NO EJECUTADO |
| HU-VEN-02a/CA-02 | AT-VEN02A-02, ST-VEN02A-01, MT-VEN02A-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:128 | NO EJECUTADO |
| HU-VEN-02a/CA-03 | AT-VEN02A-03, MT-VEN02A-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:129 | NO EJECUTADO |
| HU-VEN-02a/CA-04 | AT-VEN02A-04, ST-VEN02A-02, MT-VEN02A-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:130 | NO EJECUTADO |
| HU-CAJA-02/CA-01 | AT-CAJA02-01, ST-CAJA02-01, MT-CAJA02-01 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:136 | NO EJECUTADO |
| HU-CAJA-02/CA-02 | AT-CAJA02-02, MT-CAJA02-02 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:137 | NO EJECUTADO |
| HU-CAJA-02/CA-03 | AT-CAJA02-03, CT-CONC-05, MT-CAJA02-03 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:138 | NO EJECUTADO |
| HU-CAJA-02/CA-04 | AT-CAJA02-04, CT-CONC-05, MT-CAJA02-04 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:139 | NO EJECUTADO |
| HU-CAJA-02/CA-05 | AT-CAJA02-05, CT-CONC-02, MT-CAJA02-05 | 03_Matriz_de_Trazabilidad_y_Pruebas.md:140 | NO EJECUTADO |

## Adicionales observados, conflictos, propuestas y cursor

Véase `ETAPA-00-conflictos-planificacion.md`, que distingue observación estática, declaraciones de otras sesiones y decisiones pendientes. El índice no cambia la selección de 09 ni los resultados históricos. Próximo cursor documental: ETAPA 01, HU-AUTH-01/CA-01 (08:18), cotejarlo con el ingreso y permisos de servidor; antes de tratar HU-AUTH-02, revisar la sustitución del caso BUG-026 y registrar la vigencia de los casos de 03.
