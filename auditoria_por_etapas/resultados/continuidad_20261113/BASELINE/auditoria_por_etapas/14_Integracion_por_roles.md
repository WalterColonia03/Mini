# Prompt 14 — Recorrido completo entre roles

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 14 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos.

ALCANCE DE ESTA ETAPA: Conexiones identity, catalog, inventory, cash y sales; navegador y persistencia.
ROLES: Administrador → almacenero → vendedor → almacenero/administrador → vendedor.

TRABAJO ESPECÍFICO:
Con datos ficticios en base aislada ejecuta de extremo a extremo: administrador crea categoría/producto/proveedor; almacenero registra existencias; vendedor abre caja y cobra; almacenero contrasta stock/merma; administrador revisa movimientos y ventas; vendedor cierra caja. Agrega variantes de permisos denegados, cambios de estado, vencimiento y errores que no muten datos. Para cada paso enlaza los resultados detallados de etapas anteriores y detecta incompatibilidades entre roles, sin repetirlas como si ya estuvieran probadas.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Corrige los defectos inequívocos y documenta las propuestas de HU, criterios, tareas y pruebas que hagan falta. Si una decisión de alcance no se puede inferir, deja las alternativas documentadas y continúa con trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-14.md` y `resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
