# Inspección independiente del código para DICTAMEN-PAGOS-ASTRA

Fecha de revisión: 15/11/2026, contexto America/Lima. Subtarea de solo lectura; no constituye cierre o reapertura de etapas. Se leyeron protocolo y documentos previos de pago antes de inspeccionar producto. Se conserva Etapa 01 ingreso/bloqueo/acceso por rol y Etapa 02 sesión/personal. Cursor heredado `02-DEMO-TRAZABILIDAD-01`.

## Referencia y límites

- Repositorio: `r1-pmv`, HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`.
- El producto inspeccionado es el árbol de trabajo, NO exclusivamente ese commit. `git status --porcelain`: 207 entradas (57 modificaciones rastreadas, 150 entradas sin rastrear; directorios cuentan como una entrada).
- SHA256 de 08: `c0aa262b2dceba783ffa08e61bcca985857d777f5ef38be7749c4dd99d47e632`.
- Se inspeccionó código, rutas, plantillas y casos existentes. No se abrió DB, no se ejecutaron pruebas Django, migraciones, UI, transferencias ni publicación. Los resultados numéricos de anteriores auditorías son HEREDADOS; no se atribuyen a esta inspección.
- Las conclusiones de existencia de código son VERIFICADO DOCUMENTALMENTE mediante inspección; su comportamiento en ejecución sigue NO PROBADO por esta subtarea. Los riesgos de ampliarlo son INFERIDOS del diseño actual.

## Hallazgos propios y consecuencias

| Código actual | Evidencia precisa | Consecuencia para pagos |
|---|---|---|
| Solo existe cobro en efectivo | `sales/models.py:94` Sale, campos `cash_received`/`change_given` en 114–115; `sales/forms.py:64`; `sales/services.py:321–323,427–431` exige efectivo positivo y suficiente | No existe soporte monetario real Yape/mixto/parcial. No añadir un simple selector manteniendo esas invariantes |
| Venta y borrador son distintos | `sales/models.py:29–61` ACTIVE/DISCARDED; Sale OneToOne con borrador en 103–105 | Conservar Sale como confirmada. Pedido financiado necesita estado y persistencia diferentes al borrador descartable |
| Una caja y un borrador | `cash/services.py:48–53` fija CAJA-01 y rechaza cualquier segundo turno abierto; `sales/models.py:53–57` limita un ACTIVE por turno | Dos cajas reales requieren cambio de alcance/contrato antes de implementarlas. La asociación global del receptor debe seguir siendo segura frente a solicitudes competidoras, incluso en una caja |
| Borrador no reserva stock | `sales/services.py:112–120` y flujo de preparación; `sales/tests.py:99` contiene caso explícito | La recepción digital puede preceder a falta de stock. Diseñar conservación del abono y recuperación, no rollback supuesto del dinero |
| Descarte destruye líneas | `sales/services.py:280–301`, especialmente 298; se invoca en `identity/views.py:114`, `identity/services.py:349,467` | Logout, cambio de rol/desactivación y descarte no pueden borrar pedido con dinero recibido. Requiere protección y modificación trazable de sesión/personal |
| Precio puede actualizarse antes de rechazar cobro | `sales/services.py:391–416` actualiza líneas dentro de transacción y luego lanza ValidationError; segunda revisión bajo lock en 485–489 | Adecuado a revisión de efectivo actual; un intento digital debe congelar importe/receptor/pedido y resolver cambio como nueva versión con aceptación, conservando abonos |
| Confirmación monetaria local es atómica | `sales/services.py:434–575`: locks actor, caja, turno, borrador, productos, categorías, correlativo y lotes; creación de venta/líneas/asignaciones FEFO y descuento | Es una base reutilizable, pero solo para efectos de la DB. No incluye transferencia externa ni ledger de abonos |
| Hay idempotencia de venta | `sales/models.py:120` UUID unique; `sales/services.py:69–87,324–342,450–460`; vista `sales/views.py:207–242` recupera venta por la misma clave y montos | No confundir idempotencia de checkout con deduplicación de aviso o pago bancario. Nueva integración necesita claves y restricciones independientes |
| Relación venta–lote se conserva | `sales/models.py:171–188`; `sales/services.py:543–569` asignaciones FEFO con snapshots y control de total | Útil para devolución por lote. No existe actualmente operación de devolución/restock vinculada a reintegro |
| Caja asume toda venta en efectivo | `cash/services.py:101–109` apertura + Sum(Sale.total_amount); acumulado en `sales/services.py:496–498`; resúmenes `cash/views.py:142,165` | Si Yape se inserta en Sale sin cambiar estos contratos, se infla el efectivo esperado. La futura gaveta debe sumar movimientos físicos netos y sus reintegros explícitos |
| Plantillas anuncian solo efectivo | `sales/templates/sales/sales_receipt.html:43,82`; `sales_shift_history.html:37,48`; `sales_history.html:93,106` | Todos los desgloses, mensajes y constancias requieren HU/CA/CP antes de modificar UI |
| Constancias son internas | `sales/templates/sales/sales_receipt.html:31–32,89`; `sales_checkout.html:12` | No existe integración SUNAT acreditada por estas constancias. No convertir cálculo IGV en capacidad de emisión fiscal |
| No hay rutas de pagos parciales, anulación o reintegro | Inventario completo `sales/urls.py:5–14`; modelos y servicios leídos | Su presencia en backlog no significa IMPLEMENTADO. El descarte del borrador no es anulación de Sale ni devolución |
| Tres roles explícitos | `identity/models.py:12–18`; `identity/authorization.py:19–64` valida rol/activo; servicios vuelven a validar actor bajo bloqueo | No existe permiso delegado específico de pago/reintegro. PermissionsMixin no prueba facultades finas ya disponibles. Un permiso nuevo requiere servidor, concesión/revocación, vigencia y objetos autorizados |

## Pruebas existentes inspeccionadas, no ejecutadas

- `sales/tests.py`: efectivo exacto/insuficiente/vuelto, clave de cobro duplicada, propiedad de venta, cambios de precio y multitab.
- `sales/test_audit11_checkout.py`: formato Decimal/precisión, FEFO, reintentos divergentes, rollback de efectos locales, permisos y vínculo con caja.
- `sales/test_audit14f_allocations.py`: asignaciones de lotes, snapshots históricos y fallos posteriores a escritura con rollback.
- `sales/test_audit14closure_retry.py`: recuperación de venta histórica tras cierre.
- `cash/test_audit09_cash.py`: matriz de roles, apertura/cierre, descarte y cierre de sesión.
- `identity/test_audit02_logout_atomic.py`: rollback local del descarte y revocación de sesión.

Estos archivos no acreditan Yape, HMAC, teléfono, abono externo, reintegro ni concurrencia de un ledger de pagos inexistente. Las pruebas con TestCase tampoco acreditan por sí solas locks PostgreSQL. No se concluye que las pruebas pasan en esta revisión.

## Recomendaciones técnicas PROPUESTAS

1. Introducir un pedido persistente/snapshot y libro de abonos/aplicaciones/reintegros separado de Sale. El aviso persistido debe sobrevivir a errores de confirmación de venta.
2. No usar `cash_received = total` para simular pago digital; no insertar Sale parcialmente pagada en los informes actuales.
3. Conservar Decimal exacto y validar importes/moneda. Integridad de saldo exige constraints por registro y bloqueo transaccional al sumar/aplicar/reintegrar: un CHECK simple no controla sumas concurrentes entre filas.
4. Locks con orden documentado: cuentas/permisos cuando correspondan, pedido/abono o libro, caja/turno, productos/lotes; verificar ausencia de inversión con servicios existentes en PostgreSQL aislado. No copiar un orden de locks sin verificar todas las rutas.
5. Recibir avisos y confirmar venta en transacciones distintas. No mantener una transacción SQL abierta esperando teléfono/banco/persona.
6. Reconciliación debe separar bruto digital recibido, dinero aplicado, pasivos por no aplicado, reintegro reservado/ejecutado y efectivo físico. No reescribir cierres históricos ante pago tardío o reintegro posterior.
7. Antes de permitir nuevos estados en UI, actualizar 08 de forma aprobada y derivar vistas; no resolver omisiones con botones ocultos que carezcan de contrato.

## Huellas de los archivos principales inspeccionados

| Ruta relativa | SHA256 |
|---|---|
| sales/models.py | f0954574ef3ab4454fef943a06b0a6e6c3f699f2455e0892c4009fc5b3f5cd73 |
| sales/services.py | 5d059c83c0588363e101561e04b4f37a395a80c066d1ab3aa78708683a1c7ccd |
| sales/views.py | 6cc06ef6a3761c60fe5c9e98d9e5dc33750c19a5c56f5cca8992e4145616dee0 |
| cash/models.py | b9d18c553c5548ff2bb7b876a092bc5cd1f45bb171ebad6ee4bc3d4ee41e47dd |
| cash/services.py | 5da50fc65b915389223a24267d938a9ff64f414ad5e0ed2eb72e50ef08b07643 |
| identity/models.py | 0a7b103cbf4d4186adcbba7c9894fc2a222a6ff79bacc5bd32ba533b01789f46 |
| identity/authorization.py | ca5c4cefc371f717bcbad7d56af451fbb604aa198241b5958922015c779d0bde |
| identity/services.py | 6d633a95110681feb5e221c9a01386a2768397106e3c06a66916d91c2f7dd2fc |
| identity/views.py | ef597eada4b57d3fe90a41724cf44434a01dc29f301cbccf1aa3dcf99c38c40b |
| inventory/models.py | 2b0a7e69985dd4fc36caa6148c1f37379c4fbd6ca020593a3026ec37286fe62b |
| inventory/services.py | e869fe93ddc2137c0770a2442b096848a03ce2673a17b0b8ad8df9f32b0743d7 |

Esta nota es evidencia de inspección y propuesta. No acepta cambios de requisitos ni declara funciones implementadas/probadas.
