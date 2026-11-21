# Prompt 07 — Existencias, alertas y vencimientos

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 07 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de 08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

OBJETIVO DEL SISTEMA · 20/11/2026
Lee el contrato CT-ENTREGA-ACADEMICA en 08 y la guía auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md. El recorrido público HTTPS une ingreso por rol, lotes, venta, cobro, constancia interna e historial con el cierre de la caja única. El brief del 17/11 selecciona efectivo, digital y mixto con QR estático Yape propio y cero comisión de cobro. En auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md consta el ensayo pendiente del puente Android y del desafío del cliente. El cajero carece de facultad para acreditar por declaración. Conserva PROPUESTO / ACEPTADO / IMPLEMENTADO / PROBADO y el cursor del encabezado vigente. Al corte del 20/11, 01-K acredita su muestra local y 02-E permanece PARCIAL. Para sesiones posteriores manda el estado vigente documentado. Desarrolla solo la parte de ese recorrido asignada a esta etapa.

REGLAS PARA EVITAR FALSOS CIERRES:
Fija antes de probar la lista de requisitos/CA/CP seleccionados y sus dependencias; no reduzcas esa lista después de un fallo para aprobar. Separa revisión documental, corrección, prueba local, prueba pública y prueba monetaria real. Un requisito global no se aprueba por cuatro ejemplos de entrada. Conserva fallos y clasifica defecto de producto, prueba frágil o entorno; no repitas hasta obtener verde ocultando corridas rojas. Usa reloj/IDs controlados para empates y PostgreSQL para carreras. NO EJECUTADO, política pendiente y sublote terminado no significan etapa aprobada. Si surge un cambio, registra fundamento de aceptación y revalida dependencias; no adaptes un criterio a un bug.

ALCANCE DE ESTA ETAPA: inventory stock y catalog vencimientos; dashboard y modelos cuando sean dependencias.
ROLES: Administrador y almacenero; vendedor según permisos de consulta.

TRABAJO ESPECÍFICO:
Audita consultas de stock, alertas y HU-PROD-06; verifica fechas exactas, hoy, vencido, límites de filtro, zonas horarias, activo/inactivo, lote con cero y stock vendible frente al total físico. Contrasta indicadores, etiquetas y valores con datos guardados y con la vista de venta; detecta promesas sin sustento y riesgos de productos vencidos.

COMPROBACIÓN DE ESTA ETAPA · entrega por internet
Contrasta stock físico y vendible con vencidos, última unidad y un pedido en comprobación. Verifica lo que ve el vendedor y conserva el dinero si cambia el stock antes de confirmar. Al anular, verifica condición y lote antes de cualquier reingreso.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en 08 y regenera 07/09/03, manteniendo diseño 02 y tareas 16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-07.md` y `auditoria_por_etapas/resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
