# Prompt 12 — Constancias, historial y consultas

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 12 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de 08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

OBJETIVO DEL SISTEMA · 20/11/2026
Lee el contrato CT-ENTREGA-ACADEMICA en 08 y la guía auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md. El recorrido público HTTPS une ingreso por rol, lotes, venta, cobro, constancia interna e historial con el cierre de la caja única. El brief del 17/11 selecciona efectivo, digital y mixto con QR estático Yape propio y cero comisión de cobro. En auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md consta el ensayo pendiente del puente Android y del desafío del cliente. El cajero carece de facultad para acreditar por declaración. Conserva PROPUESTO / ACEPTADO / IMPLEMENTADO / PROBADO y el cursor del encabezado vigente. Al corte del 20/11, 01-K acredita su muestra local y 02-E permanece PARCIAL. Para sesiones posteriores manda el estado vigente documentado. Desarrolla solo la parte de ese recorrido asignada a esta etapa.

REGLAS PARA EVITAR FALSOS CIERRES:
Fija antes de probar la lista de requisitos/CA/CP seleccionados y sus dependencias; no reduzcas esa lista después de un fallo para aprobar. Separa revisión documental, corrección, prueba local, prueba pública y prueba monetaria real. Un requisito global no se aprueba por cuatro ejemplos de entrada. Conserva fallos y clasifica defecto de producto, prueba frágil o entorno; no repitas hasta obtener verde ocultando corridas rojas. Usa reloj/IDs controlados para empates y PostgreSQL para carreras. NO EJECUTADO, política pendiente y sublote terminado no significan etapa aprobada. Si surge un cambio, registra fundamento de aceptación y revalida dependencias; no adaptes un criterio a un bug.

ALCANCE DE ESTA ETAPA: sales constancia e historiales, cash historial, plantillas y permisos.
ROLES: Vendedor dueño, otro vendedor si existe, administrador y almacenero denegado.

TRABAJO ESPECÍFICO:
Audita HU-VEN-02a, 05a/05b y HU-CAJA-05. Revisa numeración, identidad, importes, historial por rol/turno, filtros reales frente a criterios y navegación directa con IDs ajenos. Verifica impresión y mensajes: constancia interna no es comprobante SUNAT. Comprueba si el reintento de cobro recupera la venta o solo redirige, y registra su efecto real. Clasifica PDF/correo o anulación según su estado de alcance.

COMPROBACIÓN DE ESTA ETAPA · entrega por internet
Con HU-VEN-02a/05a/05b y HU-CAJA-05 sigue venta → aplicaciones → abonos y devolución por origen; dos teléfonos conservan dos aportes. VENDEDOR ve solo lo suyo en turno abierto; ADMIN consulta historial/filtros. Diferencia pendiente, revisión, aplicado y devolución efectivamente entregada en vista e impresión. Verifica la leyenda interna RN-13/RN-26. Mantén el caso del profesor de 100 gaseosas Inca Kola de 3 L y recuperación dos meses después, delimitando búsquedas y documentos que realmente respalda 08, y prueba el orden de líneas empatadas.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en 08 y regenera 07/09/03, manteniendo diseño 02 y tareas 16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-12.md` y `auditoria_por_etapas/resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
