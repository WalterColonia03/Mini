# Cómo leer la planificación vigente

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

Hay74 historias:33 seleccionadas para R1 de consolidación y41 futuras. Ocho ideas excluidas conservan sus IDs pero no se presentan como historias refinadas. Se documentan110 casos que cubren219 criterios base y68 criterios complementarios/transversales. **Es cobertura de diseño, no110 pruebas ejecutadas.**

Para modificar un requisito, editar08, registrar la razón y la decisión, revisar los casos y los documentos afectados y ejecutar:

```powershell
python auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py
python auditoria_por_etapas/resultados/fuente_unica_20261112/validar_fuente.py
```

Las vistas incluyen la huella de su fuente para detectar desfases. El índice JSON es derivado, no una segunda especificación. Los importadores del corte anterior quedan protegidos para no sobrescribir esta fuente.

El historial conserva las versiones previas. **PROPUESTA → ACEPTADA → IMPLEMENTADA → VERIFICADA** son estados diferentes. Esta actualización documental no cambia código o base operativa y no cierra auditorías ni demuestra que el software ya cumpla los requisitos.
