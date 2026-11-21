# Navegador 14-H1 · primera pasada

Chrome157.0.8103.78, Playwright1.65.1, WSGI local en puerto aleatorio, SQLite temporal independiente por recorrido; es-PE/America-Lima. Cuentas y datos ficticios. El runner borra únicamente su propia base temporal al cerrar. No guarda contraseñas ni cookies/tokens; los JSON registran rutas, controles, texto y testigos sanitizados.

| Evidencia | Checkpoints / capturas | Resultado |
|---|---|---|
| [antes](antes/ejecucion.json) |3 /3|Las4comparaciones originales fueron falsas: producto, autor, proveedor y costo4. No exige que el defecto pase|
| [después, intermedia](despues/ejecucion.json) |15 /13|Fotografía y consulta móvil funcionaron; conservada como ejecución anterior|
| [final H1](final/ejecucion.json) |16 /14|4comparaciones verdaderas, carga UI3+7, renombres técnicos, ajuste UI+2, original3/disponible5, ADMIN consulta, VENDEDOR403, reenvío sin efectos, legado explícito y tabla móvil desplazada|
| [cadena general final](cadena-final/ejecucion.json) |44 /14|ADMIN crea categoría/producto/proveedor; almacenero carga3+7; vendedor abre100 y cobra14.20, almacenero merma1; admin observa5 y venta; vendedor cierra114.20 exacto|
| [recepciones final](recepciones-final/ejecucion.json) |23 /17|Carga10@3 porfixture; entradasUI10@6 y5@8, referenciasR1/R2/reintento; venta22, merma1, stock2 y cierre320; cantidades originales conservadas|

Son recorridos con cobertura solapada; no83casos independientes ni cierre completo de módulos. Las16observaciones H1 separan fixtures de maestros/renombres/ausencia histórica (preparaciónORM/SQL declarada) de accionesUI. La cadena44 demuestra el alta de maestros por administrador desde interfaz. El móvil es una ventana390×844, no un teléfono físico; escritorio1280×900. Las capturas03,10,13,13b y14 se revisan visualmente para cabecera original, cantidades, desplazamiento y legado.

Los tres recorridos finales tienen código de ejecución estable. Respecto del manifiesto final196 cambió solo inventory/test_audit14h_initial_history.py al corregir vencimientos de la fixtureFEFO; ningún modelo, servicio, vista, plantilla ni migración cambió después de esos navegadores. La compatibilidad se comprueba por archivo, no por atribuirles la huella completa posterior. 08 ejecutado `c6875fdc25bd43218891771a9990530bddc8b224a6e8dcc129ddaa8ea898250e`;08 final `1dac15a067dd0143d7b118d530f1fa222240455ec2d7d42eae83761f584fe597` conserva los criterios y agrega resultado/evidencia al caso.

Reproducción desde raíz, con Playwright disponible en el entorno temporal ya instalado:

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H-20261113/navegador/recorrido_carga.py <directorio-nuevo> --final
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido.py <otro-directorio-nuevo>
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/recorrido_recepciones.py <tercer-directorio-nuevo> --final
```

Cada carpeta tiene indice.json, ejecución, fuente08 de inicio y manifiestos de producto. El entorno temporal puede caducar; las versiones/herramientas quedan registradas para reproducirlo. Saldos/filtros/paginación no se ejecutaron como implementados; impresión física,PG,caída real y datos operativos tampoco.
