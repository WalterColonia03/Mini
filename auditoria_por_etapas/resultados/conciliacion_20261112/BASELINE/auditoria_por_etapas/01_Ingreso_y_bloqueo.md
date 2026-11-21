# Prompt 01 — Ingreso, credenciales y protección de acceso

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 01 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos.

ALCANCE DE ESTA ETAPA: identity/urls.py, views.py, forms.py, services.py, models.py, templates y pruebas.
ROLES: Visitante; cuentas de los tres roles.

TRABAJO ESPECÍFICO:
Compara HU-AUTH-01/02 y RN-17 con login. Prueba correo normalizado, cuenta activa/inactiva/inexistente, claves erróneas, cinco fallos, bloqueo de 15 minutos y tiempo restante, otra sesión, expiración y acceso correcto; revisa mensajes uniformes, CSRF, destino de redirección, persistencia y exposición de datos. Revisa límites de tráfico, acumulación de registros y acceso Django /admin/ como superficies separadas, sin presentarlos como cubiertos si no lo están.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Corrige los defectos inequívocos y documenta las propuestas de HU, criterios, tareas y pruebas que hagan falta. Si una decisión de alcance no se puede inferir, deja las alternativas documentadas y continúa con trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-01.md` y `resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
