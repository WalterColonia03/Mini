# Continuidad y segunda pasada de auditorías

Actualización:13/11/2026. Esta guía recoge la aclaración del responsable del producto: la primera pasada ha llegado hasta `12_Constancias_e_historial.md`; las etapas13,14,15,16 y17 siguen pendientes. Haber avanzado hasta12 no declara cerrados todos sus hallazgos. La organización previa de la planificación es preparación para continuar, no ejecución de17.

## Finalidad de las auditorías

El producto se construyó a partir de un backlog inicial que puede haber omitido necesidades reales del minimarket. Las auditorías deben comprobar lo existente y detectar esas omisiones: historias, reglas, permisos, integridad, arquitectura, diseño, experiencia de uso, pruebas y condiciones operativas. No se limitan a comprobar que el código reproduce un backlog incompleto.

Una recomendación debe explicar la situación operativa, usuario afectado, necesidad/beneficio, alternativas, riesgo, costo relativo, dependencias y evidencia. Se prefiere una solución proporcionada a una caja y tres roles; «profesionalizar» no justifica agregar complejidad o módulos sin necesidad. Las74 HU del corte anterior son un inventario fechado, no un catálogo cerrado ni un máximo permitido.

La planificación aceptada y versionada es el contrato que debe cumplir el software. Si se descubre que ese contrato es incompleto, contradictorio o inaplicable, se registra y resuelve el cambio con trazabilidad. No se documenta un defecto como requisito para fabricar una coincidencia, ni se presume aprobada una función por existir en el código.

## Secuencia acordada

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

Cada elemento visible se inventaría con su texto literal o plantilla y variables, rol, ruta, estado, significado esperado y referencia normativa. Un criterio puede respaldar varios mensajes; no hace falta una HU por cada frase. Si el requisito fija una leyenda literal —por ejemplo la advertencia de constancia interna—, comprobar esa redacción. Las demás variantes deben estar documentadas en el inventario y conservar exactamente el significado, condiciones y acción prometidos.

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

## Punto de entrada

Primera pasada14 **COMPLETADA para integración por roles y persistencia delimitada**,14/11/2026;634/634servidor,157checkpointsChrome y19/19PostgreSQL aislado. Los resultados anteriores permanecen en [ETAPA14](resultados/ETAPA-14.md#cierre-14) y [ESTADO_GENERAL](resultados/ESTADO_GENERAL.md). No se declara cierre de otros módulos ni segunda pasada.

**Cursor15-SEGURIDAD-BASELINE-01.** Leer protocolo/prompt15; inventariar permisos, sesiones, configuración, entorno, transacciones y recuperación contra08final/build14identificados. Clasificar como heredados los19casosPG de14, comparando archivos antes de reutilizarlos; seleccionar un sublote aislado de seguridad/recuperación. No atribuirle una corrida nueva ni aprobaciónPG17, muerte de proceso, respaldos,CI/despliegue,volumen o base operativa. Esas verificaciones siguen pendientes.

Secuencia15→16→17; después actualizar00 y segunda pasada01–17. Conservar hechos de negocio desconocidos, límites de dispositivos y normativa; no inventar una política de apertura con solo vencidos. [Protocolo](PROTOCOLO_COMUN.md) y [matriz de cobertura](resultados/soporte/14-CIERRE-cobertura.md).
