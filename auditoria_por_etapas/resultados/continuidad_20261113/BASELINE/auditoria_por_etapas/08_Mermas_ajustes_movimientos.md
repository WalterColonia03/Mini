# Prompt 08 — Bajas, ajustes y trazabilidad

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 08 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos.

ALCANCE DE ESTA ETAPA: inventory servicios, modelos, formularios, vistas de baja/ajuste y movimientos.
ROLES: Administrador y almacenero según cada operación; vendedor denegado.

TRABAJO ESPECÍFICO:
Audita HU-INV-02..06. Prueba motivo, cantidad, lotes vencidos, límites, ajuste positivo/negativo, correlativos, persistencia e historial. Comprueba impacto en stock, costos y ventas, responsables y saldo resultante; prueba rechazos sin mutación, doble solicitud y permisos. Separa pantalla de movimientos existente de historias de historial, filtros y saldo que pudieran estar incompletas. Revisa orden de bloqueos, dejando concurrencia PostgreSQL pendiente si no se ejecuta.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Corrige los defectos inequívocos y documenta las propuestas de HU, criterios, tareas y pruebas que hagan falta. Si una decisión de alcance no se puede inferir, deja las alternativas documentadas y continúa con trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-08.md` y `resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
