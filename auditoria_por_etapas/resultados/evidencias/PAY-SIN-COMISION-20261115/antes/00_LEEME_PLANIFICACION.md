# Cómo leer la planificación vigente

**Vigente DEMO-INTERNET · 15/11/2026.** Proyecto universitario con demostración mediante URL pública HTTPS. El objetivo incluye QR/Yape, efectivo/mixto, cancelaciones y operación rápida con permisos delegados, sin dueño presente para cada venta. No nuevos yapeos de devolución. Se descarta aprobación obligatoria del dueño por cada cobro; consulta Ayudantes es alternativa a evaluar, no API ni afiliación autorizada. El mecanismo de comprobación y política de reintegros siguen pendientes. [Objetivo](auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md), [escenarios/fuentes](auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md), [contrato vigente08](08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA).01-K conserva evidencia local, no aprobación del nuevo objetivo público.

Catálogo vigente:75HU,35seleccionadas y40futuras;227CA base,66criterios de contratos,4J-CA y4decoherencia visible;121CP escritos. HU-VEN-07 seleccionada y HU-VEN-10 nueva cubren Yape/mixtos;08/09 eran IDs de ideas históricas y no se reutilizan. Anulación06a/b/c requiere refinamiento de política delegada. Actualizar prompts no ejecuta auditorías.

**Antecedentes inferiores:** conservan fecha/build y alcance anterior; no sustituyen el objetivo ni estado de este corte.

## Sublote 02-E · 14/11/2026 Lima (segunda pasada acotada)

Actualización acotada de Etapa 02 (`identity`, personal y salida): `H02E-01..04` implementados y verificados (`652/652 OK`, Chrome real y `5/5` PostgreSQL `18.4`), `08` y vistas derivadas `07`/`09`/`03` regeneradas. Permanecen futuras (`W`, no disponibles) `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01`, y abiertos los controles globales de Etapa `15` (`/admin/login/`, retención/sumidero durable, IDNA y `PG 17`). [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Estado general](auditoria_por_etapas/resultados/ESTADO_GENERAL.md).

## Corte vigente14-CIERRE · 14/11/2026 Lima

Estado vigente:14 COMPLETADA en primera pasada para integración por roles;15–17 pendientes. Cursor15-SEGURIDAD-BASELINE-01. Conservar evidencias y límites históricos; al concluir17 preparar00 y ejecutar segunda pasada01–17.08 actualizado y07/09/03 reproducidos; no se declara100%delproducto.

[Informe y evidencia](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.


La **fuente principal de comportamiento del sistema** es [08 · Planificación principal del minimarket](08_Historias_de_Usuario.md). Reúne épicas, historias, MoSCoW, puntos Fibonacci orientativos, descripción, criterios de aceptación, pruebas escritas, datos y resultados esperados, reglas de negocio y decisiones operativas.

Leer una historia debe permitir saber qué debe hacer el sistema y cómo comprobarlo. Una pantalla, mensaje, ayuda, botón, estado o constancia que prometa algo también se audita contra ese contrato. Las pruebas de esta coherencia en ambas direcciones están en [CT-COHERENCIA-UI](08_Historias_de_Usuario.md#contrato-CT-COHERENCIA-UI).

| Documento | Papel vigente |
|---|---|
| [08 · Planificación principal](08_Historias_de_Usuario.md) | Única definición normativa de comportamiento, alcance y criterios |
| [07 · Reglas](07_Reglas_de_Negocio.md) | Vista derivada de las RN contenidas en08 |
| [09 · Product Backlog](09_Product_Backlog.md) | Vista derivada de selección, orden, prioridad y tamaño de las fichas |
| [03 · Matriz de pruebas](03_Matriz_de_Trazabilidad_y_Pruebas.md) | Vista derivada de criterios y casos; no demuestra ejecución |
| [01 · Proyecto](01_Proyecto_y_Releases.md), [02 · Diseño](02_Diseno_Tecnico_R1_PMV.md) | Contexto y diseño que deben satisfacer08 |
| [14 · Próximo incremento](14_Sprint_Planning.md), [16 · Tareas](16_Task_Breakdown.md) | Preparación y dependencias de ejecución, sin Sprint ficticio comprometido |
| [21 · Diferencias](21_Alcance_Actual_y_Diferencias.md), [04 · Evidencia](04_Evidencias.md) | Distancia entre requisito y producto, con pruebas y límites |
| [Estado de auditorías](auditoria_por_etapas/resultados/ESTADO_GENERAL.md) | Cobertura y pendientes; no sustituye la planificación ni autoriza cambios |

En el corte histórico12/11 había74HU:33seleccionadas y41futuras; cantidades vigentes arriba. Ocho ideas excluidas conservan sus IDs pero no se presentan como historias refinadas. Se documentan113 casos que cubren219 criterios base y68 criterios complementarios/transversales. **Es cobertura de diseño, no113 pruebas ejecutadas.**

Para modificar un requisito, editar08, registrar la razón y la decisión, revisar los casos y los documentos afectados y ejecutar:

```powershell
python auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py
python auditoria_por_etapas/resultados/fuente_unica_20261112/validar_fuente.py
```

Las vistas incluyen la huella de su fuente para detectar desfases. El índice JSON es derivado, no una segunda especificación. Los importadores del corte anterior quedan protegidos para no sobrescribir esta fuente.

El historial conserva las versiones previas. **PROPUESTA → ACEPTADA → IMPLEMENTADA → VERIFICADA** son estados diferentes. Esta actualización documental no cambia código o base operativa y no cierra auditorías ni demuestra que el software ya cumpla los requisitos.

## Continuidad de auditorías ·13/11/2026

La primera pasada completó el panel mínimo13 y los sublotes de integración14-D/E/F/G/H1/H2. La etapa14 permanece parcial, con cursor14-I-MERMA-01 en ESTADO_GENERAL. Después siguen15–17 y la segunda pasada01–17, preparando antes00. La conciliación previa fue organización documental. [Guía operativa y criterios de cierre](auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md). Las74HU son el inventario del corte, no un catálogo cerrado: el refinamiento puede agregar necesidades justificadas y sus pruebas sin crear fuentes paralelas.

Las herramientas calculan las cantidades desde las fichas y comprueban que la cabecera y los totales coincidan; no fijan un máximo de74historias. Para una HU nueva usar `anteriores:—` si no tiene estimación previa. Si un caso declara ejecución, agregar `**Evidencia de ejecución:**` con enlace al registro preciso de caso/build/resultado. La herramienta verifica la referencia, no certifica por sí sola el cumplimiento.


## Continuación14-I · 14/11/2026 Lima

Corte vigente14-I: constancia histórica e idempotencia de merma verificadas en muestra. Fuente08 y vistas07/09/03 coherentes. Primera pasada14 PARCIAL, cursor14-J-AJUSTES-HISTORIA-01; después completar14/15–17 y preparar segunda pasada01–17. No se sustituyen las fechas ni límites de resultados previos.

[Informe14-I](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).
