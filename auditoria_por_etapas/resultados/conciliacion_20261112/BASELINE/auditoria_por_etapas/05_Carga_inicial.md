# Prompt 05 — Carga inicial de existencias y lotes

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 05 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos.

ALCANCE DE ESTA ETAPA: inventory carga inicial y vínculos con catalog; consultas de lotes.
ROLES: Almacenero; administrador y vendedor según permiso real.

TRABAJO ESPECÍFICO:
Audita HU-INV-01a y RN asociadas. Prueba producto elegible, una sola carga, límites de cantidad/costo, fechas y vencimiento, varios lotes, datos erróneos y operación atómica. Verifica costo promedio, constancia, lote responsable y efectos posteriores en stock; doble envío y ausencia de mutación al rechazar. Identifica pruebas concurrentes reales requeridas y no extrapoles desde SQLite.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Corrige los defectos inequívocos y documenta las propuestas de HU, criterios, tareas y pruebas que hagan falta. Si una decisión de alcance no se puede inferir, deja las alternativas documentadas y continúa con trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-05.md` y `resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
