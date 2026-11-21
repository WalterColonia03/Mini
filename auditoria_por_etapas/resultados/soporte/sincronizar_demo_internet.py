from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
context='''**Vigente DEMO-INTERNET · 15/11/2026.** Proyecto universitario con demostración mediante URL pública HTTPS. El objetivo incluye QR/Yape, efectivo/mixto, cancelaciones y operación rápida con permisos delegados, sin dueño presente para cada venta. No nuevos yapeos de devolución. Se descarta aprobación obligatoria del dueño por cada cobro; consulta Ayudantes es alternativa a evaluar, no API ni afiliación autorizada. El mecanismo de comprobación y política de reintegros siguen pendientes. [Objetivo](auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md), [escenarios/fuentes](auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md), [contrato vigente08](08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA).01-K conserva evidencia local, no aprobación del nuevo objetivo público.

'''
details={
 '00_LEEME_PLANIFICACION.md': 'Catálogo vigente:75HU,35seleccionadas y40futuras;227CA base,66criterios de contratos,4J-CA y4decoherencia visible;121CP escritos. HU-VEN-07 seleccionada y HU-VEN-10 nueva cubren Yape/mixtos;08/09 eran IDs de ideas históricas y no se reutilizan. Anulación06a/b/c requiere refinamiento de política delegada. Actualizar prompts no ejecuta auditorías.\n\n',
 '01_Proyecto_y_Releases.md': 'AS-IS: cuaderno, demoras y dificultad para controlar empleados/dinero. TO-BE: operaciones porrol, cobros diferenciados, historial íntegro y conciliación desde aplicación publicada. No garantiza rentabilidad ni ausencia absoluta de fraude. La ampliación selecciona HU-VEN-07/10, no todos los reportes ni facturaciónSUNAT.\n\n',
 '02_Diseno_Tecnico_R1_PMV.md': '''## Diseño de pagos para refinar e implementar

La aplicación actual registra efectivo. Propuesta trazada aHU-VEN-07/10: separar intento de pago, abono recibido, aplicación a venta y reintegro; cada hecho tiene importe,estado,origen,actor,referencia e idempotencia. No basta agregar medio=MIXTO aSale. Restricciones enBD y transacciones deben proteger referencias y saldos; un abono externo no se deshace con rollbackDjango. Conservar abonos sin aplicar ante cancelación/error y recuperar estado tras timeout.

El canal externo sigue pendiente: Ayudantes ofrece consulta humana sin facultad de transferir, no una API conocida. No guardar claves bancarias ni leer notificaciones como supuesto equivalente bancario. Verificar referencia real antes de constraints definitivos; código3dígitos no único. QR/receptor controlado y versionado, no editable por vendedor. ADMIN no equivale obligatoriamente al dueño; una delegación financiera granular debe tener HU/CA/CP sin conceder administración total por comodidad.

Reintegro sin nuevoYape requiere política de medio y permisos; no mover fondos digitales a gaveta automáticamente. Migrar ventas antiguas como efectivo conocido, sin inventar abonos. Ensayar migración/reversión en copia. Para publicar: Django,estáticos,BDdurable,HTTPS y autenticación; proveedor se evalúa en15 sin compra inferida. Medir servidor y espera externa por separado; p95<=2s es propuesta a contrastar, no SLA verificado.

''',
 '14_Sprint_Planning.md': 'Preparación del incremento, sin fechas ni velocidad inventadas: línea base00 y trazabilidad02; resolver canal/refenciaYape y política de reintegros; modelo/migración de pagos; integración09–14; pruebas de abuso/concurrencia/rapidez; publicación15 y guion17. Trabajo independiente puede continuar sin habilitar dinero real. Los8SP deHU-VEN-10 son orientativos, no horas ni compromiso deSprint.\n\n',
 '16_Task_Breakdown.md': '''## Tareas DEMO-INTERNET

| Tarea | Requisito y entregable | Estado / beneficio / costo-riesgo |
|---|---|---|
| DEMO-DOC |18prompts,objetivo,HU07/10,contrato y vistas | EJECUTADA documentalmente; evita extras/cierres falsos; costo bajo |
| PAY-CANAL | Fuente legítima sin dueño presente; referencia,permisos,costo,disponibilidad | DECISIÓN PENDIENTE; Ayudantes reduce acceso al dinero, no falsedad en registro; costo no aceptado |
| PAY-REINTEGRO | Medio,casos,permiso,límite acumulado,abuso y conservación, sin nuevosyapeos | DECISIÓN PENDIENTE; evita falsas devoluciones; impacto09/12/14 |
| PAY-MODELO | Intento,abono,aplicación,reintegro,migración,restricciones,idempotencia | PENDIENTE; costo medio/alto; depende de canal/política |
| PAY-UI | QRcorrecto,referencia,total,mixto y literales en08 antes deUI | PENDIENTE; reduce doblecaptura; no anuncio de confirmación automática falsa |
| PAY-INTEGRACION | Caja,stock,constancia,historial,indicadores por componentes | PENDIENTE; evita dobleconteo y gaveta ficticia; revalidar09–14 |
| PAY-ABUSO | Empleado malicioso,QRajeno,referencia repetida,mismoimporte,revocación,carreras | PENDIENTE; controles servidor, no solo menú |
| DEMO-RAPIDEZ | Pasos,p50/p95 público y espera externa | PENDIENTE; fijar meta antes de aceptar |
| DEMO-PUBLICAR | URLHTTPS,BDdurable,migraciones,estáticos,reinicio/restauración | PENDIENTE; elegir proveedor sin gasto inferido |
| DEMO-CIERRE | Guion público,trazabilidad y resolución de fallos | PENDIENTE; no equivale a generar documentos |

Los3fallos externos01-K siguen registrados para09/10/12/14. No modificar pruebas para acomodar bugs. La aprobación personal del dueño por cada venta fue descartada.

''',
 '21_Alcance_Actual_y_Diferencias.md': 'Brecha actual: modelos/servicio/rutas/constancia representan efectivo; no hay Yape/mixtos/devoluciones demostrados. La imagenQR no prueba titularidad ni integración. No se publicóURL ni se moviódinero. HU-VEN-07/10 seleccionadas pero NO IMPLEMENTADAS; anulaciones y permisos delegados requieren refinamiento. Falta canal sin dueño y política de reintegros sin nuevosyapeos.01-K solo acredita su buildlocal; no exime la validación pública. [Registro del cambio](auditoria_por_etapas/resultados/REVISION-PROMPTS-DEMO-INTERNET.md).\n\n',
}
for name,addition in details.items():
 p=ROOT/name;s=p.read_text(encoding='utf-8')
 s=re.sub(r'^\*\*Contexto vigente 01-K[^\n]*\n\n','',s,count=1,flags=re.M)
 first,rest=s.split('\n',1)
 s=first+'\n\n'+context+addition+'**Antecedentes inferiores:** conservan fecha/build y alcance anterior; no sustituyen el objetivo ni estado de este corte.\n\n'+rest.lstrip('\n')
 if name=='00_LEEME_PLANIFICACION.md':s=s.replace('Hay74 historias:33 seleccionadas para R1 de consolidación y41 futuras.','En el corte histórico12/11 había74HU:33seleccionadas y41futuras; cantidades vigentes arriba.')
 p.write_text(s,encoding='utf-8')
p=ROOT/'auditoria_por_etapas/resultados/ESTADO_GENERAL.md';s=p.read_text(encoding='utf-8');_,rest=s.split('\n',1)
note='''# Estado general de auditorías · 15/11/2026 · objetivo DEMO-INTERNET

**Vigente:** entrega académica públicaHTTPS, cobrosQR/Yape/efectivo/mixtos y operación delegada sin dueño presente. Objetivo aceptado; **NO DESPLEGADO NI VERIFICADO** en este corte. Se actualizaron18prompts y planificación, no18auditorías. [Objetivo](../OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md), [pagos/alternativas](../PAGOS_YAPE_Y_MIXTOS.md), [informe del cambio](REVISION-PROMPTS-DEMO-INTERNET.md).

**Cursor:** `00-DEMO-INTERNET-BASELINE-01` para fijar alcance/build y dependencias; después `02-DEMO-TRAZABILIDAD-01`, conservando división01/02. En paralelo resolver `PAY-CANAL-01` (fuente legítima sin dueño; Ayudantes propuesta con costo, noAPI) y `PAY-REINTEGRO-01` (política delegada sin nuevosyapeos). Continuar trabajo independiente; no habilitar cobroreal sin resolver dependencias.

**Estados anteriores:**01-K conserva aprobación LOCAL de su alcance; la ampliación exige revalidación pública y pagos. Los3fallos externos01-K siguen abiertos en sus etapas. Las filas02–17 no se aprueban aquí. No se exige dominio comprado ni empresa real, pero sí probarURLpública en15/17.

'''
rest=re.sub(r'^\*\*Vigente01-K[^\n]*\n\n','',rest,count=1,flags=re.M)
rest=re.sub(r'^\*\*Lectura de estados anteriores:[^\n]*\n\n','',rest,count=1,flags=re.M)
s=note+rest.lstrip('\n')
s=re.sub(r'(?m)^(\| \[01\][^\n]*)$',lambda m:m[1].replace('**100% CERRADA Y APROBADA para demostración local del alcance definido**','**CERRADA LOCAL01-K; publicación DEMO-INTERNET pendiente de revalidación**').replace('`02-LOCAL-TRAZABILIDAD-01`','`01-DEMO-PUBLICO-01` tras disponer del build público'),s)
p.write_text(s,encoding='utf-8')
print('Contexto, diseño, tareas, sprint y estado sincronizados')
