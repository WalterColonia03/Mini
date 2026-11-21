# Servidor 14-H1 · primera pasada

Base SQLite en memoria nueva por corrida; APP_ENV=test y configuración sustituida antes de django.setup. No se leyó ni migró la base operativa. Python3.12.10, Django5.2.18, SQLite3.49.1. Build final196 archivos `f9a593aacbd4cd5a0c753d672b5e06c1ada3dd21fb8a2f16b68009ee03f866aa`. Comando desde la raíz:

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H-20261113/servidor/regresion.py <directorio-nuevo>
```

| Ejecución preservada | Resultado | Interpretación |
|---|---|---|
| [corrida-1](corrida-1/regresion-final.txt) |589/591;1fallo+1error;86.190s|Expectativas anteriores de costo2 y contexto subsequent_lots; actualizadas conforme a08. Siete tests nuevos pasaron|
| [final, intermedia](final/regresion-final.txt) |591/592;1fallo;99.743s|La fixture añadida exigía salida del loteA con igual vencimiento y posible instante empatado. FEFO podía elegirB porUUID. Se separaron vencimientosA/B/POST; no se alteróFEFO|
| [final2, vigente](final2/regresion-final.txt) |592/592 OK|Fuentes estables, sin migraciones pendientes de generar. [Manifiesto](final2/regresion-manifiesto.json)|

Ocho tests nuevos en inventory/test_audit14h_initial_history.py: fotografía ante renombres/ajuste/recepción/venta/merma; proveedor ausente/cantidad999999/costo9999999.9999/número64/escapeHTML; vencimiento y producto inactivo; legado sin original; cuatro fallos postwrite; rol/fecha/estado/repetición; consulta/alias/cache/GET/POST; migración. Cuatro puntos postwrite guardaron antes de lanzar excepción: cabecera, lotes, líneas, promedio. Se contrastan26 tablas de negocio de catalog/inventory/cash/sales; sesiones/login quedan fuera de esa igualdad.

Migración inventory0008→0009 conserva columnas y filas anteriores, añade cabecerasNULL y cero líneas inferidas; la prohibiciónSQL de modificar received_at permanece. No se simuló corte real del proceso ni carreraPG ni reversión con datos nuevos. Las relaciones y snapshots dependen del servicio para consistencia transversal; no se certifican ante escrituras arbitrarias.

La suite global incluye pruebas históricas que se reejecutan; no sustituye cobertura navegador ni aprueba todas las HU. [Caso](../../../../../08_Historias_de_Usuario.md#CP-HU-INV-01a-003) · [Matriz acotada](../criterios-final.json).
