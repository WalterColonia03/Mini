# Prompt 03 — Catálogo y ciclo de vida del producto

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 03 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de 08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

OBJETIVO Y CONTEXTO VIGENTES:
Lee `auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md` y el contrato `CT-ENTREGA-ACADEMICA` de 08 antes de aplicar conclusiones históricas. La meta es una demostración universitaria mediante URL pública HTTPS, con Yape por QR, efectivo/mixto, cancelaciones y control de empleados, sin depender del dueño presente para cada venta. El cierre 01-K solo acredita su alcance local; no acredita internet ni pagos nuevos. No se exige comprar dominio ni inventar una empresa real. Cada comportamiento/literal debe estar en HU/CA/CP; no agregar funciones, diagnósticos, umbrales de tráfico o políticas legales solo por criterio del auditor.

REGLAS PARA EVITAR FALSOS CIERRES:
Fija antes de probar la lista de requisitos/CA/CP seleccionados y sus dependencias; no reduzcas esa lista después de un fallo para aprobar. Separa revisión documental, corrección, prueba local, prueba pública y prueba monetaria real. Un requisito global no se aprueba por cuatro ejemplos de entrada. Conserva fallos y clasifica defecto de producto, prueba frágil o entorno; no repitas hasta obtener verde ocultando corridas rojas. Usa reloj/IDs controlados para empates y PostgreSQL para carreras. NO EJECUTADO, política pendiente y sublote terminado no significan etapa aprobada. Si surge un cambio, registra fundamento de aceptación y revalida dependencias; no adaptes un criterio a un bug.

ALCANCE DE ESTA ETAPA: catalog/ y formularios, modelos, servicios, plantillas y rutas del tramo.
ROLES: Administrador y almacenero; vendedor solo en consultas de venta autorizadas.

TRABAJO ESPECÍFICO:
Audita HU-CAT-01..04 y HU-PROD-01..05 y RN pertinentes. Examina lista, alta, edición, activación, categoría, precio con IGV, código, stock mínimo, búsqueda y mensajes, valores extremos y duplicados. Evalúa si la planificación se limita a enlatados y si la interfaz permite otros productos. Comprueba impacto de desactivar producto/categoría en borrador, inventario e históricos; clasifica edición/eliminación de categorías o escáner por su alcance real.

ACTUALIZACIÓN ESPECÍFICA DEMO-INTERNET:
Prueba que el cajero no pueda modificar precio/categoría/estado por petición directa; cambios autorizados de precio invalidan un resumen de cobro previamente revisado. No inventar descuentos o productos por peso para justificar la UI. Medir búsqueda/captura dentro del recorrido rápido del cajero sin omitir validación de stock/precio.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en 08 y regenera 07/09/03, manteniendo diseño 02 y tareas 16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-03.md` y `auditoria_por_etapas/resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
