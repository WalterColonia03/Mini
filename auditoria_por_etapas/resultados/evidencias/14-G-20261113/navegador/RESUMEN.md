# Navegador 14-G · recepción conectada

Primera pasada,13/11/2026 Lima. Chrome157.0.8103.78/Playwright1.65.1, HTTPWSGI loopback con middleware/CSRF, tres contextos1280×900, es-PE/America-Lima. Cada recorrido crea una SQLite temporal y cuentas ficticias; se elimina al cerrar. Los testigos consultan todas las tablas de negocio en solo lectura, publicando campos sin secretos y huellas; no se consultó la base operativa.

## Diagnóstico antes de cambios

`antes/` conserva una corrida incompleta en el selector: el arnés buscó una etiqueta sin el código del producto. Se corrigió el selector usando la opción observada. No se atribuye ese fallo al producto. `antes2/` completó9checkpoints. Fixture declarada: producto/proveedor/cuentas creados porORM, carga10@3 confirmada mediante servicio. EnUI, primera recepciónC10@6 dejó20@4.5000, pero devolvió carga inicial; no habíaUUID en formulario. El reintento igual dio error de lote existente. Segunda entrega realC5@8 fue rechazada. La misma clave cambiando aD11 añadiómercadería. Renombrar proveedor/autor cambió la constancia. [Comparación](antes2/comparaciones.json) · [Ejecución](antes2/ejecucion.json).

## Corte final2 · 23 checkpoints

1. ALMACENERO registraC10@6 con proveedor: R1,20unidades/4.5000. Reenvío de igual contenido recupera la misma ruta sin mutación.
2. Nueva entregaC5@8 sin proveedor: R2,25unidades/5.2000. ADMIN observa ambas procedencias; ADMIN/VENDEDOR no acceden al registro. Reenvío con contenido divergente rechaza sin mutar.
3. Control técnico de fixture renombra proveedor y almacenero. La constanciaR1 conserva los originales; recarga no muta. ADMIN consulta y VENDEDOR recibe403.
4. Cantidad0 conservaUUID y no muta; fecha vencida y fecha contradictoria paraC rechazan sin mutar.
5. VENDEDOR abre100, vende22×10=220 con efectivo220/vuelto0. Asignación real: inicial10,R1 diez,R2 dos. Stock3 y costo5.2000.
6. ALMACENERO identificaR2 en selección de merma y retira1; stock2. ADMIN observaR1/R2, venta y merma, consulta ventas. VENDEDOR cierra320 exacto. R1 conserva10UND y promedio histórico4.50 tras las salidas.

Los cambios de maestro son controles técnicos sobre la fixture, no prueba de UI de edición. La prueba específica no repite altas por interfaz: esa cobertura está en la cadena general nueva. [Ejecución](final2/ejecucion.json) · [Comparación](final2/comparaciones.json) · [Movimientos y testigo](final2/20-movimientos-tras-venta-merma.json) · [Cierre](final2/22-cierre.json).

Build188fuentes `3c1b9ec10f99e695122fbae37451bd0e0462ae601a1f1cc8deca910035b32af3`, estable y compatible por archivo con el build194 del producto. Se inspeccionaron capturas de constancia, selección de origen y movimientos; el dato histórico y el actual se distinguen. `despues/` y `final/` conservan cortes intermedios. La accesibilidad integral, impresión, móvil/dispositivos y todas las fronteras siguen con sus alcances; no se declaran verificadas por esta muestra.

## Cadena general · 44 checkpoints nuevos

`cadena-final/` reutiliza el arnés14-D en base nueva y build14-G. ADMIN crea categoría/producto/proveedor porUI; ALMACENERO carga3+7@2; VENDEDOR abre100 y cobra14.20 (efectivo20/vuelto5.80), ALMACENERO descuenta merma1, ADMIN observa stock5/movimientos/venta y VENDEDOR cierra114.20. Incluye permisos por navegación yPOST directo, categoría inactiva/reactivada, vencimiento, efectivo insuficiente, causa/cantidad de merma inválidas y venta sin turno. [Ejecución](cadena-final/ejecucion.json). Los datos14D identifican la fixture reutilizada, no una aprobación heredada; el build y la ejecución son14-G.

## Reproducción

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/recorrido_recepciones.py auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/repeticion-nueva --final
```

La rutaPYTHONPATH es la instalaciónPlaywright de esta sesión; adaptarla en otro equipo y disponer deChrome. E14_CHROME permite indicar ejecutable. El script reutiliza el soporte14-D conservado, elige puerto libre y exige carpeta nueva. `recorrido_recepciones_inicial.py` conserva el arnés de9pasos deantes2/despues. Para la cadena general ejecutar14-D/navegador/recorrido.py con carpeta nueva dentro14-G. Los JSON y capturas se indexan porSHA256 al cerrar el corte.
