# Disposiciones01-E · 14/11/2026

## Aceptación y límite

El usuario encargó auditoría01 y correcciones de producto solo dentro del alcance identity/urls,views,forms,services,models,templates y pruebas. DOC-02-04 vigente ya exige correo254 y fronteras en todas las capas. La precisión en08 y `LoginForm(max_length=254)` aplican ese contrato, sin nueva política: **ACEPTADA, IMPLEMENTADA y VERIFICADA EN MUESTRA**;120/120testsidentity y acceso real254 enBraveUI22, detalle en ETAPA-01. Antes se aceptaban identificadores255–320 imposibles como cuentas normales y se persistían intentos inútiles. Beneficio: coherencia de campo/servidor y menos registros inválidos; riesgo bajo de rechazar identificadores que nunca fueron cuentas válidas; costo bajo; sin migración. Se conserva la prueba anterior, se modifica su expectativa por el contrato fechado y se añade acceso real con254, sin borrar evidencia para fabricar verde.

No se acepta por existir código ni por redactar propuesta. Nuevas decisiones cuantitativas permanecen **PROPUESTAS/INVESTIGACIÓN**. No se necesita HU nueva para cada control técnico; reutilizar AUTH01/02 y DOC01-06/DOC02-04.

| ID reutilizado / recomendación | Beneficio / alternativa | Riesgo / costo / impacto / estado |
|---|---|---|
| DOC01-06/C01: deshabilitar admin en entrada comercial o canal de mantenimiento separado | Evita autenticación alternativa; elegir deshabilitar si no hay uso operativo de mantenimiento | P1, costo bajo–medio; requiere arquitectura/despliegue y cuentas técnicas reales. Contrato ACEPTADO, configuración concreta PENDIENTE; no tocar producción |
| SEC-15-TRAFICO-01: medir presupuesto por punto de entrada/IP fiable más identidad | Contiene CPU/hash y ataque con identificadores distintos; alternativa proxy o middleware compartido | P1, costo medio; NAT puede bloquear tienda entera, XFF no fiable puede evadir; no inventar tasas. Investigación y pruebas de redes compartidas pendientes |
| SEC-15-RETENCION-01: separar estado activo y bitácora, diagnóstico de volumen/plazo | Controla crecimiento; alternativa archivo agregado vs TTL validado | P2, costo medio; borrar fallos1–4 o fila en uso altera RN17/concurrencia. Política real y PG requeridos, no borrar datos |
| SEC-15-OBS-01 / DOC01-06/C02–03: eventos sanitizados tras resultado transaccional y requestID | Permite investigar bloqueo/error sin secretos; alternativa tabla específica con emisión trascommit | P1, costo medio; evento parcial o falso éxito, retención/privacidad; prueba de fallo de registrador y canario exc_info pendiente |
| DOC02-04: diagnóstico Unicode/punycode antes de IDNA, conservar sanción al renombrar | Evita cuentas equivalentes ambiguas y bypass al cambiar correo | P1, costo medio; colisiones/impacto en datos/sesiones; identidad estable y carreras de02/15 pendientes |
| AUTH01/02 RN17: investigar máximo razonable de clave/cuerpo antes de hash | Acota recursos sin truncar contraseña | P2, costo bajo–medio; no bloquear claves históricas válidas ni fijar72 arbitrariamente; caracterización volumen y política pendiente |
| CT-COHERENCIA-UI: mantener mensaje uniforme y minutos redondeados; distinguir contador enviado de reloj vivo | Evita prometer precisión/actualización inexistente | Costo bajo; no introducir JS o HU nueva sin necesidad; verificar ancho estrecho/teclado y lector con entorno real en siguiente sublote |

Corrección254 afecta alta/edición solo como dependencia contractual, no modifica sus flujos. Revalidar regresión identity y campos de ingreso en navegador; métricas/pantallas comerciales y sus reglas quedan fuera. Sesión única/remota/recuperación y LOG UI siguen futuras. No se mide seguridad por suma de pruebas verdes: tres probes de01-E pasan precisamente al reproducir admin alternativo/acumulación/retención.
