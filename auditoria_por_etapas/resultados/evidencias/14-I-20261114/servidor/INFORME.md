# Servidor14-I · 14/11/2026 Lima · primera pasada

Comando desde la raíz, con un directorio de salida nuevo:

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-I-20261114/servidor.py <directorio-nuevo>
```

El runner configura SQLite `:memory:` antes de django.setup; APP_ENV=test y secreto efímero. No usa credenciales ni base operativa. Con argumentos posteriores admite etiquetas Django; `--migration` solo genera la migración local sobre configuración aislada. Python3.12.10, Django5.2.18, SQLite3.49.1. Los manifiestos incluyen inicio/finUTC y hash08/build. No se guardan secretos.

| Ejecución conservada | Resultado | Interpretación |
|---|---|---|
| [migración](migracion/resultado.txt) |0010_writeoff_history generada|9campos nullable; claveUUID única, sin backfill. Cambios de fuente esperados en esta tarea, no una prueba estable|
| [focal-1](focal-1/resultado.txt) |32tests;6fallos/subcasos|Dos aserciones nuevas buscaban nombres en toda la página e incluían el usuario del menú. Se acotan a la constancia. Las otras expectativas exigían404/redirección antigua; actualizadas contra CA04, no rebaja del requisito|
| [regresión-1](regresion-1/resultado.txt) |614tests;4fallos/2errores,77.895s|Imports faltantes en tests adaptados, claveHTTP ahora requerida, redirects antiguos y comparación de migración no contemplaba camposNULL nuevos. Se preservan los logs completos|
| [regresión-2, final](regresion-2/resultado.txt) |**614/614**,79.261s; sin migración pendiente|Fuentes estables; [manifiesto](regresion-2/manifiesto.json).604anteriores+10nuevos. No equivale a614casos de navegador|

Diez pruebas nuevas `inventory/test_audit14i_writeoff_history.py`: historia tras editar maestros; reenvío entre clientes/sesiones y tras estado/fecha;11variantesHTTP inválidas;8variantes de tipos/clave/causa/detalle de servicio; vencimiento/robo de producto inactivo; origenR2 frente aR1del mismoC; legado; tres excepciones postwrite; roles/métodos/revocación; escapeXSS y explicación larga; reenvío tras agotar lote. Los subcasos se solapan; no se suman comoHU.

El testigo de servidor compara todas las21tablas catalog/inventory/sales/cash, incluidas cantidades/costos/huellas/snapshots; el navegador añade membresía y activación de los actores. No se incluyen secretos de Account ni tablas técnicas de sesión/auth/admin. Tres fallos ocurren después de crear la baja, después de guardar stock y después de restablecer costo al agotar: revierte todo y permite reintentar la mismaUUID. No prueba caída real del proceso ni pérdida de disco.

La prueba de migración heredada14-E se amplía para comprobar explícitamenteNULL en los9campos nuevos y conservación exacta del resto del registro previo; ejecuta migración desde0006aúltimo. Las pruebas de origenH1/G y protección de received_at siguen pasando. No se aplicó0010a ninguna base operativa.

Las adaptaciones07/08 y inventory/tests añaden laUUID en positivos y esperan la constancia exigida. INV05/06 globales siguen404/futuras. Los negativos específicos nuevos aseguran que la clave requerida no enmascare reglas de fecha/cantidad/causa. No se alteran saldos/esperados para aprobar una pérdida.

NO EJECUTADO: dosconexionesPostgreSQL concurrentes con mismaUUID o venta/baja/ajuste; colisiones/agotamiento delcorrelativoB; caída real; escritura privilegiada directa de snapshots; volumen/SLA; migración/diagnóstico de datos operativos. El bloqueo transaccional y la restricciónúnica son implementación, no evidencia de esos escenarios.
