# Prompt 15 — Seguridad, despliegue y confiabilidad

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 15 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

ALCANCE DE ESTA ETAPA: identity, config, services transaccionales, compose, documentación de seguridad y tests.
ROLES: Los tres roles, usuario anónimo y eventualmente personal autorizado de Django.

TRABAJO ESPECÍFICO:
Revisa permisos servidor vs menú, CSRF, sesiones, contraseñas, bloqueo de ingreso, acceso /admin/, logs, secretos, HTTPS, backup/restauración y configuración de despliegue. Diseña y ejecuta pruebas de concurrencia con PostgreSQL si existe entorno aislado: ventas, lotes, mermas, ajuste, correlativos, caja e inicio de sesión; registra bloqueo, resultados, posibles interbloqueos y evidencia. Si no existe, deja casos y comandos pendientes; no uses SQLite como prueba de bloqueos ni afirmes certificaciones. No expongas secretos ni afectes servicios del usuario.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en08 y regenera07/09/03, manteniendo diseño02 y tareas16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-15.md` y `resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
