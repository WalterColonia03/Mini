# Verificación acotada del soporte aislado — 09/11/2026

Se corrigió el lanzador de auditoría, no la aplicación: antes de solicitar contraseña o enviar login/POST, `audit00.py http` exige una respuesta HMAC a un desafío aleatorio del middleware instalado solamente por `audit_settings.py`. La clave permanece local y no se escribe en esta evidencia. Un servicio ajeno, un servidor anterior o uno detenido no acredita identidad. Esta verificación reduce el riesgo de enviar datos o solicitudes a otro servicio que ocupe 8765; no es una certificación de seguridad del equipo ni prueba frente a un proceso que lea la clave local.

También se impidió que `prepare` migre una base SQLite existente cuando falta la marca `prepared.json`; en ese caso requiere inspección manual. Cuando existe la marca, sigue rehusando resembrar.

Desde la raíz del proyecto se ejecutó con el servidor auditado arrancado con `audit00.py serve`:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/verify_identity.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit00.py' check
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit00.py' inspect
```

Resultado: prueba HMAC válida aceptada; comparaciones con prueba vacía y prueba fabricada rechazadas; HTTP GET sin credenciales ni POST. `check`: cero incidencias; `makemigrations` dry-run: sin cambios. `inspect`: tres cuentas, una categoría, un producto sin lotes/turnos/ventas; SHA256 de la base original coincide con preparación. Se repitió `prepare` ya marcado: rechazó el resembrado. La rama que rechaza una base sin marca se verificó por lectura; no se creó una base artificial para probarla.

Al intentar `verify_identity.py` contra el servidor aislado anterior, sin el middleware nuevo, la prueba HMAC falló, como era esperado. Se identificaron por línea de comando y detuvieron únicamente las instancias `audit00.py serve` del trabajo de auditoría; con el servidor detenido se ejecutó `audit00.py http`: salió con código 1 e informó que no podía verificar el servidor, antes de solicitar contraseña o enviar POST. La consulta de procesos no mostró instancias `audit00.py serve` después del cierre.

La prueba de 25 comprobaciones HTTP del sublote 00-A **no se volvió a ejecutar** después de este cambio. Para reproducirla, reiniciar el servidor de auditoría para cargar el middleware y ejecutar el comando `http` del lanzador tras comprobar la base y conservar la evidencia anterior; requiere la contraseña ficticia de las tres cuentas. La evidencia `00-persistencia.json` se actualizó al repetir `inspect` y conserva el mismo estado observado.
