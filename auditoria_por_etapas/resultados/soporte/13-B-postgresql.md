# 13-B-04 · PostgreSQL aislado · primera pasada,13/11/2026

**37/37 comprobaciones aprobadas y6/6 tests de regresión**, conjuntos solapados. [Resultado final](../evidencias/13-B-PG-20261113T165253183453Z/results.json) · [Regresión](../evidencias/13-B-PG-20261113T165253183453Z/regression-postgresql.txt). Build de identity/views y versión08 constan en cada JSON; el manifiesto final de etapa relaciona el conjunto. Motor PostgreSQL18.4 x64 Windows, READ COMMITTED; **difiere del17 previsto**, no certifica17 ni despliegue.

## Protección y repetición

`r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/soporte/audit13_pg.py` crea siempre cluster nuevo en TEMP `audit13-pg-<azar>`, marcaAUDIT13_OWNED, base de nombrealeatorio y puerto libre en127.0.0.1. No aceptaDSNexterno, no carga.env del operador, comprueba nombre ydata_directory; autenticaciónSCRAM, secreto fuera de logs/evidencias. Detiene exclusivamente el cluster marcado y verifica puerto cerrado enfinally. No elimina las bases anteriores. Clusters finales detenidos. El argumento histórico `pre` omite volumen; no reproduce código antiguo después de la corrección.

## Defecto y corrección

[Precorrección](../evidencias/13-B-PG-20261113T163815572545Z/results.json):5/5 intercalaciones reprodujeron métricas incompatibles. El lector ya había contado6lotes próximos; otro backend confirmó simultáneamente dos cambios en una transacción, y las consultas siguientes observaron4críticos y67.16. No era únicamente retraso de actualización: ninguna instantánea completa tenía esa combinación.

La precisión técnica se incorporó primero en08. `_dashboard_summary` compone una sola sentenciaSELECT con agregados y subconsultas generadas porORM, parámetros enlazados, misma fechaLima,0consultas paraVENDEDOR y1paraADMIN/ALMACENERO. No cambia aislamiento global ni abre una transacción durante la navegación. La conversión monetaria conserva los conversoresDecimal del backend.

Revalidación:5/5 intercalaciones devuelven un estado completo. Además25lecturas mientras un hilo escritor independiente confirma22transacciones alternadas: todas pertenecen al estado anterior o posterior, sin mezcla. PIDs independientes y todos los resultados quedan registrados. Esto prueba la muestra concurrente y el snapshot de sentencia; no una instantánea de toda página, de enlaces posteriores ni atomicidad de otros módulos.

## Exactitud y alcance

Siete cifrasADMIN iniciales3/60.06/5.06/1/3/6/5, tresALMACENERO3/6/5 y ausenciaVENDEDOR. Límites del díaLima por snapshots anterior/inicio/último microsegundo/siguiente día; fecha siguiente cambia a1/92.22. Inventario3/6/5, vencimientos30→11filas, historial del día3/60.06. Las fechas imposibles/noISO y cadenas de5000caracteres deD11 se rechazan sin filas. En una transacción revertida se vaciaron realmente ventas/lotes/productos/turnos: panel e inventario/vencimientos/historial mostraron sus ceros y mensajes correctos. Los6tests ejecutan también fallo/recuperación y fronteras de fechas.

En fixture nueva, servicios reales: borrador2×3.55 conserva resumen y lote3; cobro total7.10/efectivo10.00/vuelto2.90 produceADMIN4/67.16/5.06/1/4/6/5, almacén4/6/5 y lote1. Repetir misma clave de idempotencia y consultar de nuevo conserva seis ventas de todas las fechas y lote1. **No es cobro por navegador.**

## Medición proporcionada

Se añadieron2000productos,20000lotes y30000ventas sintéticas de0.01; total2008/20014/30006. Suma diaria exacta367.16 de30004ventas; descuentos5.06.21mediciones secuenciales por rol conBDlocal calentada: ADMIN mediana40.61ms/p95muestral52.75ms/máximo62.31ms; almacén20.06/25.79/27.97ms. Vendedor no emiteSELECTde negocio. No son tiemposHTTP ni carga multiusuario niSLA. [SQL yEXPLAIN ANALYZE/BUFFERS](../evidencias/13-B-PG-20261113T165253183453Z/) conservados por rol. No se añadió índice ni caché: estos tamaños y tiempos no demuestran necesidad productiva. Volumen real/SLA siguen investigación operacional.

Se conservan intentos intermedios:164714 falló por doble setup_test_environment del arnés;164812/164933/165202 son ejecuciones anteriores a la ampliación final. No se suman resultados como casos únicos ni se borran fallos. PostgreSQL17, carga productiva y aceptación visual quedan fuera de lo demostrado.
