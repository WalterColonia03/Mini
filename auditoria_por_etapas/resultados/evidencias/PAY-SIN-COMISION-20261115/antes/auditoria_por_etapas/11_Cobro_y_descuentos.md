# Prompt 11 — Cobro efectivo, Yape, mixto e integridad

Copia el bloque siguiente en un nuevo chat o continuación, en orden. Si ya se trabajó una parte, retoma desde el cursor de `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` y el informe de esta etapa.

```text
Trabaja en `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`. Ejecuta la etapa 11 de auditoría del sistema del minimarket. Lee y aplica `auditoria_por_etapas/PROTOCOLO_COMUN.md` completo y consulta `auditoria_por_etapas/resultados/ESTADO_GENERAL.md` si ya existe. El objetivo es profundizar en esta etapa, sin presentar como terminados otros módulos. Consulta también `auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md`: registra primera o segunda pasada, versión de 08, build, alcance y cursor; conserva la evidencia anterior y distingue lo revalidado de lo heredado.

OBJETIVO Y CONTEXTO VIGENTES:
Lee `auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md` y el contrato `CT-ENTREGA-ACADEMICA` de 08 antes de aplicar conclusiones históricas. La meta es una demostración universitaria mediante URL pública HTTPS, con Yape por QR, efectivo/mixto, cancelaciones y control de empleados, sin depender del dueño presente para cada venta. El cierre 01-K solo acredita su alcance local; no acredita internet ni pagos nuevos. No se exige comprar dominio ni inventar una empresa real. Cada comportamiento/literal debe estar en HU/CA/CP; no agregar funciones, diagnósticos, umbrales de tráfico o políticas legales solo por criterio del auditor.

REGLAS PARA EVITAR FALSOS CIERRES:
Fija antes de probar la lista de requisitos/CA/CP seleccionados y sus dependencias; no reduzcas esa lista después de un fallo para aprobar. Separa revisión documental, corrección, prueba local, prueba pública y prueba monetaria real. Un requisito global no se aprueba por cuatro ejemplos de entrada. Conserva fallos y clasifica defecto de producto, prueba frágil o entorno; no repitas hasta obtener verde ocultando corridas rojas. Usa reloj/IDs controlados para empates y PostgreSQL para carreras. NO EJECUTADO, política pendiente y sublote terminado no significan etapa aprobada. Si surge un cambio, registra fundamento de aceptación y revalida dependencias; no adaptes un criterio a un bug.

ALCANCE DE ESTA ETAPA: sales cobro, modelos/servicios, caja e inventory; tests de integración.
ROLES: Vendedor, con verificación posterior por administrador y almacenero.

TRABAJO ESPECÍFICO:
Audita HU-VEN-01c, descuentos y RN de venta. Prueba cantidad y precio, efectivo insuficiente/exacto/excedente, descuento válido y límites, redondeo/base/IGV, FEFO, vencimiento, idempotencia, doble envío, cambio de precio/stock entre pantallas y reversión sin afectación ante error. Comprueba advertencia tributaria antes de confirmar y los efectos atómicos en venta, lotes y caja; identifica corrección o requisitos faltantes de descuentos. No presentes como probada concurrencia real sin PostgreSQL.

ACTUALIZACIÓN ESPECÍFICA DEMO-INTERNET:
Auditar HU-VEN-01c, HU-VEN-07, HU-VEN-10 y RN-02, además del efectivo existente. Ejecutar matriz de pagos:QR correcto/ajeno, referencia inequívoca vs código de 3 dígitos, comprobación receptor, mixto, dos abonos, faltante/exceso, captura falsa, duplicado, dos clientes, mismo importe, POST alterado, precio/stock cambiado, idempotencia y timeout. Un campo marcado por el cajero no es evidencia bancaria. Resolver consulta delegada sin dueño presente; Ayudantes Yape es alternativa pendiente de afiliación/costo y no una API. No ejecutar transferencias reales por herramientas; ensayos humanos pequeños con importe/destinatario acordados. No prometer devolución por nuevo yapeo.

Primero identifica y clasifica cada HU, criterio, regla, tarea, pantalla, ruta, acción, mensaje, campo y salida de este tramo. Audita planificación → comportamiento y comportamiento → planificación, en navegador y con datos aislados, siguiendo el protocolo. Comprueba el servidor y los efectos entre roles, no solo la apariencia. Detecta omisiones legítimas del backlog inicial y documenta recomendaciones de HU, RN, criterios, arquitectura, diseño, requisitos no funcionales, tareas y pruebas con beneficio, riesgo, costo e impacto. Usa las autorizaciones del usuario de esta sesión y la delegación vigente: corrige producto solo dentro de ese alcance; este archivo no lo autoriza por sí mismo. Una propuesta no se acepta automáticamente por redactarla ni por existir en el código. Integra lo aceptado en 08 y regenera 07/09/03, manteniendo diseño 02 y tareas 16 coherentes; registra el fundamento de aceptación y revalida los módulos afectados. Si faltan hechos del negocio o hay una decisión no cubierta por la autorización, registra alternativas y continúa el trabajo independiente.

Entrega y actualiza `auditoria_por_etapas/resultados/ETAPA-11.md` y `auditoria_por_etapas/resultados/ESTADO_GENERAL.md`, con evidencia reproducible, resultados de pruebas, pendientes, cobertura y cursor exacto. Si la etapa es demasiado grande, termina un sublote coherente y continúa desde el cursor en la siguiente sesión. No confundas no ejecutado con aprobado ni declares coincidencia total sin evidencia.
```
