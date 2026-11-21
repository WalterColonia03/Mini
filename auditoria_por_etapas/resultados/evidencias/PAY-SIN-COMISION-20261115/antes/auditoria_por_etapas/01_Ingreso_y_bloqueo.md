# Prompt 01 — Ingreso, credenciales y protección de acceso

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 01 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de 08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

OBJETIVO Y CONTEXTO VIGENTES:
Lee `auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md` y el contrato `CT-ENTREGA-ACADEMICA` de 08 antes de aplicar conclusiones históricas. La meta es una demostración universitaria mediante URL pública HTTPS, con Yape por QR, efectivo/mixto, cancelaciones y control de empleados, sin depender del dueño presente para cada venta. El cierre 01-K solo acredita su alcance local; no acredita internet ni pagos nuevos. No se exige comprar dominio ni inventar una empresa real. Cada comportamiento/literal debe estar en HU/CA/CP; no agregar funciones, diagnósticos, umbrales de tráfico o políticas legales solo por criterio del auditor.

REGLAS PARA EVITAR FALSOS CIERRES:
Fija antes de probar la lista de requisitos/CA/CP seleccionados y sus dependencias; no reduzcas esa lista después de un fallo para aprobar. Separa revisión documental, corrección, prueba local, prueba pública y prueba monetaria real. Un requisito global no se aprueba por cuatro ejemplos de entrada. Conserva fallos y clasifica defecto de producto, prueba frágil o entorno; no repitas hasta obtener verde ocultando corridas rojas. Usa reloj/IDs controlados para empates y PostgreSQL para carreras. NO EJECUTADO, política pendiente y sublote terminado no significan etapa aprobada. Si surge un cambio, registra fundamento de aceptación y revalida dependencias; no adaptes un criterio a un bug.

ALCANCE DE ESTA ETAPA: identity/urls.py, views.py, forms.py, services.py, models.py, templates y pruebas.
ROLES: Visitante; cuentas de los tres roles.

TRABAJO ESPECÍFICO:
Compara HU-AUTH-01/02 y RN-17 con login. Prueba correo normalizado, cuenta activa/inactiva/inexistente, claves erróneas, cinco fallos, bloqueo de 15 minutos y tiempo restante, otra sesión, expiración y acceso correcto; revisa mensajes uniformes, CSRF, destino de redirección, persistencia y exposición de datos. Revisa límites de tráfico, acumulación de registros y acceso Django /admin/ como superficies separadas, sin presentarlos como cubiertos si no lo están.

ACTUALIZACIÓN ESPECÍFICA DEMO-INTERNET:
Conserva ingreso/bloqueo separado de personal02. Revalida en la URL pública cookies, CSRF, destino, errores, roles y persistencia tras reinicio; identifica build exacto y datos aislados. `/admin/` es superficie separada; no reactivar por comodidad. Las observaciones de tráfico/ciclo de registros no autorizan nuevos límites ni plazos legales; solo aplicar requisitos técnicos aceptados y proporcionales al entorno público.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en 08 y regenera 07/09/03, manteniendo diseño 02 y tareas 16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-01.md` y `auditoria_por_etapas/resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
