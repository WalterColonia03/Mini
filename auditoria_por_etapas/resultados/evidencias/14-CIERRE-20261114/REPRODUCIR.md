# Reproducción y comprobación visual · 14-CIERRE

Primera pasada,14/11/2026 Lima. Todas las carpetas finales registran versiones, hashes, UTC, testigos de tablas y resultado. Utilizar una ruta de salida nueva: los runners rechazan sobrescribir ejecuciones. No ejecutar `manage.py migrate` contra configuración operativa; los runners configuran su base aislada antes de iniciar Django.

Desde `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`, PowerShell:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor.py' 'auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/servidor/repeticion-NUEVA'
```

Configura SQLite en memoria y ejecuta toda la suite y makemigrations --check --dry-run. La corrida final registró634pruebas/132.064s. Los casos focales pueden pasarse después de la salida: `inventory.test_audit14j_adjustments cash.test_audit14closure_money catalog.test_audit14closure_price sales.test_audit14closure_retry`. Los conjuntos se solapan.

Para Chrome, Playwright1.65.1 estaba instalado en un directorio temporal añadido aPYTHONPATH; en otro equipo debe instalarse en un entorno de pruebas equivalente, sin usar ni cambiar datos operativos. Chrome157 se invoca con channel=chrome, headless. Cada script crea SQLite temporal y WSGIloopback; contraseña aleatoria no se guarda.

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& './r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/recorrido_ajustes.py' 'auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/navegador/repeticion-ajustes-NUEVA'
```

| Script / argumentos adicionales | Corrida final |
|---|---|
|14-D-20261113/navegador/recorrido.py SALIDA|navegador/cadena-final,44|
|14-CIERRE-20261114/recorrido_ajustes.py SALIDA|navegador/ajustes-final,31|
|14-I-20261114/recorrido_merma.py SALIDA --final|navegador/merma-final,26|
|14-H2-20261114/navegador/recorrido_kardex.py SALIDA --final|navegador/kardex-final,20|
|14-CIERRE-20261114/recorrido_dinero.py SALIDA|navegador/dinero-final,13|
|14-CIERRE-20261114/recorrido_precio.py SALIDA|navegador/precio-final-2,8|
|Runner copiado en complementos-chrome-2, consultar suINFORME|complementos-chrome-2,15|

El prefijo común es `auditoria_por_etapas/resultados/evidencias/`. [Fuentes exactas preservadas](runners-final/manifiesto.json). El runnerbase escribe su propio hash; no confundirlo con hash de cada Journey derivada. ParaPg19 y diagnóstico histórico4 ver [PostgreSQL](postgresql/INFORME.md) y [migraciones](postgresql/MIGRACIONES.md): clúster18.4 temporal,PID/esperas registradas; diagnóstico4 usaSQLite/migraciones históricas, no se atribuye aPG.

Comprobación documental sin acceder a bases:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/verificar.py'
```

Ese verificador compara archivos por hash, reproduce vistas en memoria, confirma criterios y enlaces; escribe build-final/validacion-final. No reejecuta funcionalidad ni convierte evidencia anterior en nueva. `preparar_plan.py` y `cerrar_documentacion.py` son scripts de aplicación única ya ejecutados, no pasos para repetir pruebas.

## Inspección visual

Se inspeccionaron imágenes reales deChrome: resumen de errorJ02con foco visible/enlace al campo, nuevo loteQ0J19con costo/fuente y origen, historia móvilJ30a390px sin desborde del detalle, cierreM12con10m/diferencia0 y aviso de revisiónP04precio10→12. Las capturas finalesJ19/M12/P04 corresponden al buildcongelado. El agente complementario inspeccionó selectores vacíos, claves inválidas y Kardex con origen ambiguo; informes en su carpeta. No se deduce accesibilidad integral ni comportamiento de dispositivos físicos de estas capturas. Menú móvil tiene desplazamiento horizontal propio; no se presenta como navegación móvil integral aprobada.

Los errores de claves ocultas forzadas conservan textoUUID deDjango y etiqueta técnica; se prueba petición manipulada, no un campo de operación que deba completar el usuario. No hay secretos en los datos ficticios registrados. Las carpetas diagnósticas se conservan con estadoincompleto y se excluyen del total157.

Comprobación de diferencias: git diff --check informó líneas en blanco finales en catalog/forms.py e identity/tests.py; ambas ya existían en producto-antes.zip (CRLF CRLF). Son formato heredado, sin corrección funcional pendiente; no se atribuye una comprobaciónGit limpia. Las advertencias LF/CRLF no alteraron el build congelado.

