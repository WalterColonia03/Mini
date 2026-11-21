# Chrome14-I · 14/11/2026 Lima · primera pasada

WSGI real en127.0.0.1, middleware/CSRF, tres cuentas ficticias y contextos independientes. Cada runner creaSQLite temporal y la elimina al acabar, conservando testigos sanitizados por checkpoint. Chrome157.0.8103.78, Playwright1.65.1, Django5.2.18. No se conecta a operación.

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-I-20261114/recorrido_merma.py <directorio-nuevo> --final
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido.py <otro-directorio-nuevo>
```

La dependenciaPlaywright está en ese directorio temporal y puede caducar; deberá disponerse de esa versión al reproducir. `recorrido_merma_diagnostico.py` conserva la variante previa; reproducir defectos requiere el producto delZIP inicial en una copia separada, no restaurarlo sobre cambios posteriores.

| Corrida | Estado y evidencia |
|---|---|
| [diagnóstico-1](diagnostico-1/ejecucion.json) |8pasos; fallo del arnés buscandoCSRF en página sin formulario; no fallo delproducto|
| [diagnóstico-2](diagnostico-2/ejecucion.json) |11pasos; duplicación ya registrada; falloORM bajo contextoasyncPlaywright al preparar renombrado|
| [diagnóstico-3](diagnostico-3/ejecucion.json) |12pasos/6capturas; [defectos reproducidos](diagnostico-3/diagnostico.json): sin constancia, doblebajaenotras sesión, autor/loteactuales en historia. Control de renombrado usaSQL aislado, no edición porUI|
| [final-1](final-1/ejecucion.json) |Interrumpida enI10 por expectativa fijaB1; fixturelegadoyaocupaba unregistro. Se captura la referencia devuelta, no se cambia contador/producto|
| [final-2, vigente](final-2/ejecucion.json) |**26checkpoints/17capturas**,01:28:26–01:28:38Lima; fuentesestables. El campo descriptivo `sublote` conserva por error «diagnóstico»; es elrecorrido con`--final` y aserciones finales. No se reescribe esa evidencia|
| [cadena-final, vigente](cadena-final/ejecucion.json) |**44checkpoints/14capturas**,01:28:26–01:28:42Lima; fuentesestables. Nombres14D identifican lafixture reutilizada, no lafecha/build de ejecución|

Ambosfinales ejecutan08`a7f22f243fef0087d5d5b3b807b9c53b9ee6b9a0a701eec953a4b3298c79c27d` y build delmanifiestoChrome`cd148c66cc77dd2d1994e4d6048a2250f5c1a5bd75b939873c1effef35e1a1df` (195fuentes). La huella canónica deproducto completo incluye otro conjuntodearchivos; comparar porarchivo, noigualarhashes de algoritmosdistintos.

## Específico de merma

Fixture declarada porservicios/ORM: A10@3; producto de vencimientoE3@4al díaLima; producto deorígenes con10@3másR1C10@6yR2C5@8; legado sinfotografía. La confirmación/rechazos/consulta se hacen porChrome; los renombrados y desactivaciónextra son controlesSQL explícitos en esaSQLite.

- I01..05: exceso11, detallevacío y vencimientoprematuro no mutan; daño2deA deja8yconstancia, costo3.0000. Cambian soloLot/StockWriteOff, precio/ventas/caja/promedio intactos.
- I06..11b: mismaUUID enmisma/nuevasesión devuelve original; divergenciarechaza; vendedorGET/POST403; ADMINve−2/saldo8. Una sola baja2.
- I12..16: trasrenombrarmaestros, Kardexyconstancia mantienen autor/lote/productooriginales; recarga; vendedor403 y POSTconstancia405 sinmutación.
- I17..18: botónImprimir despacha`window.print`instrumentado ymedioprintreal ocultan controles. Capturaescritorio1280×900ymóvil390×844 sinoverflowdelapágina. No impresora ni navegador móvil físico.
- I19..25: UUIDotroactorrechaza; dañodevencido yrobo sindetalle rechazan; robo/vencimientoconproductoinactivo admitidos; baja1deR2deja4yR1conserva10; legado muestra datos conocidos yNo disponible sin inventarnombres.

Las capturasI13/I17/I18/I25 ycadena32/34/38se inspeccionaron visualmente: fotografía/leyendainterna, impresiónsinmenú, botonesmóviles, ausenciadelegado, saldos/caja. Fechas/UUID son ficticios; sincontraseñasni tokens.

## Cadena completa y límites

ADMINcrea categoría/producto/proveedor por menús; ALM carga3+7@2; VENDEDORabre100, prepara4×3.55, rechazaefectivo14.19, cobra14.20 con20yvuelto5.80; ALMcontrasta6ymerma1; ADMINve5yventa; VENDEDORcierra114.20exacto, recargayno vende sinturno. Se recorren denegaciones, desactivación/reactivación decategoría yfechavencida/causeincompatible sinmutación según checkpoint. La constatación posterior de8deAmerma es independiente deesta cadena, no mezclarfixtures.

Los testigos cubren21tablas denegocio y membresía/activación deusuarios. Se conserva literalvisible/controles/valores/ruta/rol/HTTP porpaso. Los70checkpointsse solapan; no son70criterios distintos. Losotrosestados/campos/pruebasPG demódulos previos son heredados o noejecutados, no aprobados por reutilizar unrunner. Impresión física, lector pantalla, todoslosanclajes/teclado, límitecantidad999999enChrome ytextolargomóvil no seejecutaron.
