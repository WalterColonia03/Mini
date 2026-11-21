# Prompt 06 — Entradas posteriores frente a reposición

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 06 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de 08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

OBJETIVO DEL SISTEMA · 20/11/2026
Lee el contrato CT-ENTREGA-ACADEMICA en 08 y la guía auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md. El recorrido público HTTPS une ingreso por rol, lotes, venta, cobro, constancia interna e historial con el cierre de la caja única. El brief del 17/11 selecciona efectivo, digital y mixto con QR estático Yape propio y cero comisión de cobro. En auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md consta el ensayo pendiente del puente Android y del desafío del cliente. El cajero carece de facultad para acreditar por declaración. Conserva PROPUESTO / ACEPTADO / IMPLEMENTADO / PROBADO y el cursor del encabezado vigente. Al corte del 20/11, 01-K acredita su muestra local y 02-E permanece PARCIAL. Para sesiones posteriores manda el estado vigente documentado. Desarrolla solo la parte de ese recorrido asignada a esta etapa.

REGLAS PARA EVITAR FALSOS CIERRES:
Fija antes de probar la lista de requisitos/CA/CP seleccionados y sus dependencias; no reduzcas esa lista después de un fallo para aprobar. Separa revisión documental, corrección, prueba local, prueba pública y prueba monetaria real. Un requisito global no se aprueba por cuatro ejemplos de entrada. Conserva fallos y clasifica defecto de producto, prueba frágil o entorno; no repitas hasta obtener verde ocultando corridas rojas. Usa reloj/IDs controlados para empates y PostgreSQL para carreras. NO EJECUTADO, política pendiente y sublote terminado no significan etapa aprobada. Si surge un cambio, registra fundamento de aceptación y revalida dependencias; no adaptes un criterio a un bug.

ALCANCE DE ESTA ETAPA: inventory stock_entry, servicios y planificación de reposiciones.
ROLES: Almacenero y administrador; vendedor denegado.

TRABAJO ESPECÍFICO:
Contrasta HU-INV-01b, HU-SOL-01..05b, RN-01 y alcance: distingue la recepción directa seleccionada de una solicitud futura. Comprueba proveedor, lotes, costo promedio, recepción total/parcial y vínculos documentales solo si existen. Identifica conflicto y consecuencias; no elimines la regla ni conviertas la entrada directa en proceso aprobado sin una decisión sustentada. Registra las historias de reposición futuras separadas de lo ejecutable.

COMPROBACIÓN DE ESTA ETAPA · entrega por internet
Verifica en 08 la recepción directa seleccionada con autorización comercial externa y separa las HU-SOL futuras. Prueba origen de lote/costo y desempate FEFO por fecha, recepción e ID. Reponer mercadería aumenta existencias. La reposición de billetes pertenece a 09 y no crea lotes.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en 08 y regenera 07/09/03, manteniendo diseño 02 y tareas 16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-06.md` y `auditoria_por_etapas/resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
