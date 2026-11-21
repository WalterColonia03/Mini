# 13-B-03 · Servidor · primera pasada13/11/2026 Lima

> El 13/11/2026 se comprobó la compatibilidad de estas ejecuciones con el build visual final. Los pendientes visuales que se mencionan en este registro quedaron cubiertos en el recorrido posterior. [Comparación de hashes](../evidencias/13-B-final-20261113/validacion-evidencia.json) · [Evidencia de navegador](13-B-final-navegador.md).

[Poblado100/100](../evidencias/13-B-servidor-20261113T164755068835Z/results.json) · [Vacío100/100](../evidencias/13-B-servidor-20261113T164757087079Z/results.json) · [Regresión ampliada160/160](../evidencias/13-B-20261113/regresion-final.txt). Los conjuntos se solapan; no sumarlos como360pruebas únicas. SQLite aislada, Django5.2.18/Python3.12.10, cuentas ficticiasADMIN/ALMACENERO/VENDEDOR. CadaJSONregistra fechaLima, fixture, versión08 y hashes de cinco archivos producto; estos corresponden al producto final. Cambios posteriores de08 registran evidencia, sin alterar la selección funcional.

## Reproducir

Preparar `audit13_run.py new` y `new empty`, fijarAUDIT13_RUN_DIRa la carpeta marcada, ejecutar `audit13b_queries.py` en cada una. Rechaza fixture consumida por cobros. No carga.env operativo. Usar nuevas bases para cualquier integración. Los tests de regresión usan base temporal independiente yAUDIT13_DEFAULT_COOKIES=1. Se ejecutaron catalog.test_audit03_catalogue, inventory.test_audit07_stock_expirations, cash.test_audit09_cash, identity, sales.test_audit12_receipts_history, sales.test_audit13_history_boundaries ysales.test_audit11_checkout. No hubo fallos en160tests del build final.

## Cobertura y correcciones

- Panel:7/3/0claves, valores de la fixture, fechaLima, vacío real, métodosPOST/HEAD405. Cuenta inactiva pierde sesión, rol inválido403 y anónimo302, sin resumen expuesto.
- D06/D07: omitido/vacío/espacios,1/3650,0/negativo/3651,decimal/signo/Unicode/nulo/repetido,5000dígitos y5000ceros iniciales. Cuenta/lista mantienen5vencidos y2/6/8próximos según1/30/3650; inválidos retornan30con aviso.
- D10/D11: siete clases de mensajes; fechas imposibles/noISO/desborde9999-12-31, extremos representables0001-01-01/9999-12-30, rango invertido, identificadores inválidos/desconocidos, correlativo5000caracteres, fecha exacta/rango diario. [Pre91/97](../evidencias/13-B-servidor-20261113T163916359558Z/results.json): cinco500y una aceptaciónnoISO. Corregido `_history_date` con formato/fecha/rango representable explícitos; no modificación de venta ni política comercial.
- GET/POST denegados al vendedor en stock/vencimientos/catálogo y al almacenero en ventas/turnos/empleados; sin datos protegidos. Huella de tablas de negocio idéntica antes/después, excluye sesiones/mensajes. Invalidez de cuenta se revierte en transacción.
- Panel/stock/vencimientos/historial: fallo simulado produce500sin ceros ni diagnóstico; siguiente consulta200. En tres destinos se inyectó excepción al render, no se cortó físicamente laBD: prueba de manejo HTTP, no disponibilidad de infraestructura. Página500autónoma distingue consulta de operación y explica recuperación.
- Textos: historial todas las fechas+ayudaFecha exacta, igualdad del mínimo, mercadería recibida. Verificados servidor, **pendientevisualfinal**.

Se conservan corridas97/97anteriores y100/100posteriores a consulta única. Las dependencias revisadas no equivalen a auditoría completa de ventas,caja,catálogo oinventario. Los errores de filtro no prueban rendimiento adversarial ilimitado. [Bloqueo y siguiente recorrido visual](13-B-navegador.md).
