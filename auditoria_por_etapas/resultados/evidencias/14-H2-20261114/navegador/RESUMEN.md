# Navegador14-H2 · 14/11/2026 Lima

Primera pasada; Chrome157.0.8103.78, Playwright1.65.1, WSGI loopback/puertoaleatorio, SQLite temporal independiente; datos ficticios, es-PE/America-Lima. Contraseñas yCSRF no se guardan. CadaJSON conserva texto/controles/ruta/rol ytestigo denegocio; manifiestos registran versión y fuentes.

| Carpeta | Observaciones/capturas | Resultado |
|---|---|---|
| [antes](antes/ejecucion.json) |3/3|Filtro y página ignorados, sin saldo; trescomparaciones de defecto verdaderas|
| [despues](despues/ejecucion.json) |5/3|Incompleto: runner esperaba«Seleccione» yDjango mostraba«Escoja». Producto rechazó opción inválida; no se cambia elmensaje paraaprobar|
| [final](final/ejecucion.json) |20/15|Funcional completo; revisiónvisual descubrió lotes y−22partidos enmóvil|
| [final2](final2/ejecucion.json) |20/15|Incluye degradaciónlectura, antes deCSSfinal|
| [cadena-final](cadena-final/ejecucion.json) |44/14|Cadena general antes deCSSfinal|
| [final3 vigente](final3/ejecucion.json) |20/15|Saldos/filtros/páginas/roles/legado/desajuste yCSSmóvil verificados|
| [cadena-final2 vigente](cadena-final2/ejecucion.json) |44/14|Revalidaciónconectada de ADMIN hasta cierre deVENDEDOR sobre runtimefinal|

El casoKardex prepara maestros ymovimientos porORM/servicios con relojcontrolado:10@3,R1C10@6,R2C5@8, venta22ymerma1;estadospersistidos ylecturaChrome son reales,pero no se atribuye altaUI aesa fixture. La cadena44sícrea categoría/producto/proveedor porADMIN, carga3+7 porALMACENERO, abre100/vende4×3.55=14.20 porVENDEDOR, merma1deja5,ADMINcontrasta yVENDEDORcierra114.20sin diferencia.

ChromeKardex prueba menú→consulta, saldos10/20/25/3/2, filtro10:01..13:00soloVenta conapertura20/cierre2/variación−22/saldo3,recarga/limpiar,períodoincompleto/invertido,tipo/páginainválida/fuera,parámetrorepetido,vacío conapertura/cierre2,25+1ajustesempatadosconvariación26ypreservaciónparámetros,lecturaALMACENERO,403VENDEDOR,POST405sinmutación,móvil390×844ytable-scroll,legadoNo disponible ydesajusteinducidoSQLquenofinge saldo. Las lecturas/rechazoscomparan huellas; la modificaciónSQLfinal esun control técnico declarado, no operación deusuario.

Capturas finales02/12/17/18/19/20 revisadas para semántica ysaldos, navegación, legibilidad móvil yavisos. La correcciónCSS mantiene ancho300del detalle, tabladesplazable y−22enunalínea. Escritorio1280×900; móvil esun viewport, no teléfonofísico. No se afirma impresión ni accesibilidadcompleta.

Fuente08 ejecutada `4c46f42530b25499e4f4cf31426e9fafd9293b95efdbddb38ed74403ae2e7e77`; final `d2e03f10c190cf6a631152b35fa110d863d0fb3276723f6e7e95e8a0451ffa4a`. Los manifiestos de final3 ycadena-final2 coinciden porarchivo conelbuildfinal198 `3bed2cd9e85e61dfe2dae607e438a83be911950ec328de59ac596b407155b1f6`;ambosrecorridosestables. La fuente08finalañade resultados sin cambiar lossietecriterios. Las64observaciones finalestienenalcance solapado; no64HU/criterios.

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H2-20261114/navegador/recorrido_kardex.py <directorio-nuevo> --final
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido.py <otro-directorio-nuevo>
```

El entornoPlaywrighttemporalpuedecaducar; lasversionesestánregistradas. `recorrido_kardex_inicial.py` conserva elrunnerprevioconexpectativalocalizadaerrónea. Sin--final, elrunner soloregistradiagnóstico; reproducirel«antes» requiere elproductoarchivado. No se restauró automáticamente sobretrabajoposterior.
