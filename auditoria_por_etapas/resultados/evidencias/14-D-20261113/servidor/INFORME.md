# Revalidación de servidor 14-D · 13/11/2026

Primera pasada, continuación de 14-A/B/C. Este anexo profundiza las conexiones identity, catalog, inventory, cash y sales mediante solicitudes WSGI al servidor Django en proceso y comprobación de persistencia. La evidencia visual se registra en el sublote de navegador. La unidad de aprobación aquí es el caso enumerado.

## Entorno, alcance y reproducción

Python 3.12.10, Django 5.2.18, SQLite 3.49.1, zona America/Lima. El runner fuerza una base nueva SQLite `:memory:` antes de inicializar Django y aplica migraciones. Cada ejecución crea tres cuentas ficticias con contraseña aleatoria, inicia sesión por el formulario HTTP y usa CSRF válido. Los productos, lotes y categoría se crean por las rutas normales. Los cambios de estado administrativos se confirman por HTTP y la revisión del cobro se obtiene del HTML servido. El vencimiento se simula adelantando `timezone.localdate` un día dentro de un contexto acotado. Su salida declara el día real y el día simulado.

La función `snapshot` calcula huellas de todos los campos y filas de 21 tablas de las cinco aplicaciones, incluidas claves, cantidades, importes, tiempos y relaciones M2M de identidad. Exporta las huellas y los nombres de tablas cambiadas, sin credenciales ni tokens. Las tablas técnicas de sesión, auth, admin y migraciones quedan fuera de esta medición. Un rechazo exige igualdad de las 21 tablas. S16 comprueba la mutación autorizada y limita las tablas afectadas. Hay un control positivo posterior que cobra 10.00, deja 7 unidades de 10 tras una baja y la venta de dos unidades, y cierra con esperado 20.00 y diferencia 0.00.

```powershell
# Desde la raíz de planificación. Usar un nombre de salida nuevo en cada ejecución.
r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/variantes.py auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/repeticion-nueva.json

# Desde r1-pmv. El test runner crea y destruye exclusivamente su base de prueba.
$env:APP_ENV='test'
$env:DJANGO_DEBUG='false'
$env:PYTHONUTF8='1'
.venv/Scripts/python.exe manage.py test --verbosity 1

# Desde la raíz de planificación. La inicialización fuerza :memory: antes de checks.
r1-pmv/.venv/Scripts/python.exe -c "import runpy; ns=runpy.run_path('auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/variantes.py'); ns['call_command']('check'); ns['call_command']('makemigrations', check=True, dry_run=True)"
```

Las respuestas y huellas por paso están en [antes](variantes-antes.json) y [después](variantes-despues.json). El runner reproducible es [variantes.py](variantes.py). El build general y la versión de 08 se vinculan desde el informe principal 14-D. El JSON contiene además la huella específica del servicio de merma.

## Casos y trazabilidad

El inventario de rutas, campos y mensajes del flujo se completa en el anexo14-D de inventario. Esta tabla enlaza los 18 casos de servidor con su requisito. Se aplicó el contrato vigente antes de evaluar el resultado.

| Caso | Actor y operación | Requisito que respalda la expectativa | Antes | Después |
|---|---|---|---|---|
| S01 | ADMIN solicita carga inicial con producto válido | RN-29, HU-AUTH-01/CA-04, HU-INV-01a | 403 y huella igual | CUMPLE |
| S02 | ALMACENERO solicita apertura de caja | RN-29, HU-CAJA-01 | 403 y huella igual | CUMPLE |
| S03 | VENDEDOR solicita baja de lote real | RN-29, HU-INV-02 | 403 y huella igual | CUMPLE |
| S04 | VENDEDOR solicita estado de producto | RN-29, HU-PROD-05 | 403 y huella igual | CUMPLE |
| S05 | ALMACENERO solicita cobro con revisión válida | RN-29, HU-VEN-01c | 403 y huella igual | CUMPLE |
| S06 | VENDEDOR paga 9.99 para total 10.00 | HU-VEN-01c/CA-01, RN-30 | 200 con error y huella igual | CUMPLE |
| S07 | VENDEDOR cierra con borrador de dos unidades | HU-CAJA-02/CA-04 | 200 con error y huella igual | CUMPLE |
| S08 | VENDEDOR cobra después de desactivación de producto por POST ADMIN | HU-PROD-05/CA-01, HU-VEN-01c/CA-03 | Rechazo y huella igual | CUMPLE |
| S09 | VENDEDOR cobra después de confirmación de desactivación de categoría | J-CA2, HU-VEN-01c/CA-03 | Rechazo y huella igual | CUMPLE |
| S10 | ADMIN reenvía confirmación con versión antigua | J-CA3 | 409 y huella igual | CUMPLE |
| S11 | ALMACENERO solicita baja 11 con físico 10 | HU-INV-02/CA-01 | Rechazo y huella igual | CUMPLE |
| S12 | ALMACENERO solicita Vencimiento de lote que vence mañana | RN-05, CP-HU-INV-02-001 | INCUMPLE, 302 y baja 1 | CUMPLE, 200 y huella igual |
| S13 | VENDEDOR cobra después de alcanzar el día de vencimiento | RN-03, HU-VEN-01c/CA-03 | Disponible 0 y huella igual | CUMPLE |
| S14 | ALMACENERO solicita Daño explicado de lote vencido | HU-INV-02/CA-02, RN-05 | Rechazo y huella igual | CUMPLE, mensaje corregido |
| S15 | ALMACENERO solicita Robo de lote vencido sin explicación | HU-INV-02/CA-03, RN-05/C-01 | INCUMPLE, orienta a Vencimiento | CUMPLE, pide detalle y huella igual |
| S16 | ALMACENERO solicita Robo explicado de lote vencido | HU-INV-02/CA-02, RN-05/C-01 parcialmente | INCUMPLE, impide causa real | CUMPLE para causa, responsable y saldo |
| S17 | VENDEDOR reenvía cobro confirmado | HU-VEN-01c/CA-05 | Una venta y huella igual | CUMPLE |
| S18 | VENDEDOR intenta cerrar otra vez | HU-CAJA-02/CA-03 | Rechazo y huella igual | CUMPLE |

S16 cubre causa/autor/saldo y conserva fecha del lote. La ausencia de constancia dedicada y costo histórico de salida impide aprobar RN-05/C-01 completo, HU-INV-02/CA-04 y RN-05/C-03. La prueba HTTP adicional en la suite repite el rechazo/aceptación para ADMIN y ALMACENERO, verifica cantidad, precio, promedio de un lote, detalle, autor, fecha, caja y ventas, y reenvía la misma clave después de corregir errores. La concurrencia PostgreSQL queda pendiente de la etapa 15.

## Hallazgos y correcciones

**H14D-S01, prioridad alta, resuelto en el alcance de causa de merma.** RN-05 y HU-INV-02/CA-02 vigentes permiten robo explicado de un lote vencido. El servicio rechazaba toda causa distinta de vencimiento, y permitía descartar por vencimiento unidades aún vigentes. S12 demostró una mutación indebida de stock, producto y merma. S15/S16 demostraron el rechazo y la orientación equivocada. La corrección usa la fecha local de Lima para restringir Daño a vigente y Vencimiento a caducado, conserva Robo con detalle obligatorio y muestra instrucciones compatibles con la causa real. El formulario ya ofrecía los tres motivos y transmitía los errores del servicio. La autorización de corrección acotada fue delegada por el agente principal durante esta sesión, con fundamento en08 y el pedido de auditoría. Se modificó `inventory/services.py` sin cambios de esquema.

La prueba heredada de medianoche de etapa 08 exigía rechazar Robo vencido. Se actualizó al contrato vigente, conservando [fuentes previas](antes-correccion-merma/) y evidencia pre. Dos fixtures usaban Vencimiento de lotes vigentes para probar efectos ajenos a la causalidad. Ahora usan Robo explicado. Se añadió una prueba HTTP de regresión en `inventory/test_audit08_writeoffs_adjustments_movements.py` porque la omisión previa permitía que ambas contradicciones pasaran la suite. La prueba de huecos de funcionalidad mantiene sus verificaciones de ausencia y sigue siendo evidencia de pendientes.

**H14D-S02, prioridad media, resuelto por el agente principal.** El test C16 obtenía la última venta con orden descendente de UUID. La corrida previa produjo dos lecturas de V-00000001, aunque se habían creado dos ventas. La corrección obtiene la venta por la clave de idempotencia enviada, verifica redirección a su recibo y correlativo consecutivo exacto. La regresión final lo ejecutó con éxito. Este fallo era de prueba y su aprobación anterior requería esa precisión.

## Revisión independiente de descuentos

Se inspeccionaron `sales/forms.py`, `sales/views.py`, `sales/services.py`, `sales/templates/sales/sales_checkout.html` y los cambios de pruebas de etapas 09/11/12 y C16.

- `CheckoutForm` valida la ausencia o cero, rechaza valores no permitidos y parámetros múltiples antes de operar. El formulario servido dejó de ofrecer un descuento.
- `checkout_sale` conserva la validación de actor e importes, permite recuperar una venta ya confirmada con sus montos originales y rechaza descuentos de nuevas ventas antes de modificar datos. La ruta exige propietario, vínculo con borrador, subtotal, efectivo y descuento compatibles para recuperar la constancia.
- La prueba histórica reproduce venta 20 con descuento 2 y total 18, verifica su recuperación por servicio y HTTP, y vuelve a recuperarla después de cerrar. Mantiene snapshot de venta y acta. El cierre incluye 18.00 en el total.
- La prueba nueva de descuentos registra igualdad de siete tablas para entradas rechazadas, incluye positivo, negativo, formato, notación y duplicado, y un cobro sin descuento con aritmética exacta. La nueva plantilla estima vuelto con enteros de centavos y conserva el bloqueo de doble envío y la recuperación de controles en `pageshow`.

No se identificó un fallo nuevo en esa revisión. Su evidencia dinámica se encuentra en los tests ejecutados por la regresión final. La estimación visual y el JavaScript requieren además la evidencia de navegador del sublote correspondiente.

## Resultados y límites

| Ejecución | Resultado | Evidencia |
|---|---|---|
| Regresión heredada previa | 558 aprobadas de 559, falla C16, 74.016s | [regresion-antes.txt](regresion-antes.txt) |
| Variantes con huellas antes | 15 de 18 cumplen | [variantes-antes.json](variantes-antes.json) |
| Variantes con huellas después | 18 de 18 cumplen para expectativas de la tabla | [variantes-despues.json](variantes-despues.json) |
| Regresión acotada inventario, etapas 07/08 | 58 de 58, 6.006s | [regresion-inventario-despues.txt](regresion-inventario-despues.txt) |
| Regresión integral final, incluidas 14-A/B/C | 560 de 560, 81.487s | [regresion-final.txt](regresion-final.txt) |
| Django check y makemigrations --check --dry-run | Sin incidencias ni cambios de esquema, SQLite en memoria | [check-final.txt](check-final.txt) |

Los conjuntos se solapan y el numerador de pruebas aprobadas no mide criterios completos. La regresión incluye pruebas de ausencia de funcionalidades pendientes. Los 119 tests A/B/C conservan valor de servidor y HTML en su alcance.

Las pruebas iniciales 01–11 de 14-A usan objetos y transacciones separados, y 07–10 revisan 200 sin vincular la misma venta y merma. C01/C02 de 14-C cambiaban el estado con ORM, sin ejecutar la acción administrativa. Estas limitaciones justificaron S08/S09 y el recorrido conectado en navegador. El informe previo trataba la interacción real como opcional, pero el protocolo vigente exige ejecutarla o marcarla NO EJECUTADO. El anexo de navegador determina su cobertura.

Permanecen pendientes la trazabilidad contable y el costo de salida completo, la constancia de merma, el modelo de asignación histórica por lote, recepción independiente de carga inicial, permisos exhaustivos fuera de las muestras y las carreras PostgreSQL. El siguiente cursor del servidor es RN-05/C-01 y C-03 con dos lotes de costo distinto y consulta de la salida histórica, coordinado con DOC-03AH-01 y DEC-11-MODELO-AUDITORIA-VENTAS. Este anexo deja esos requisitos en PARCIAL o NO EJECUTADO según su caso.

