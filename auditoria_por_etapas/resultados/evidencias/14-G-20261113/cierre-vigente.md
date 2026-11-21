<!-- Fragmento insertado en resultados/ETAPA-14.md; enlaces relativos a ese destino. -->
<a id="vigente-14-g"></a>
## Estado vigente14-G · 13/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. Sublote14-G concluido para recepción propia, reintento, procedencia e historia de ingresos nuevos.** Se corrigieron identidad de recepción, fotografía de proveedor/autor/cantidad original y compatibilidad del lote comercial repetido con ventas/bajas/ajustes. El próximo cursor es **14-H-KARDEX-SALDOS-01**. No se declaran terminados los módulos dependientes.

[Informe14-F preservado](evidencias/14-G-20261113/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-G-20261113/antes-ESTADO_GENERAL.md). Los resultados anteriores conservan build/alcance. La nueva cadena general repite altas de maestros hasta cierre; el caso de recepción usa una fixture inicial declarada. Los dos recorridos tienen bases independientes.

### Versiones y entorno

| Elemento | Corte14-G |
|---|---|
|08 inventariado/ejecutado|SHA256 `8d4a7cbede73eac5b09524363e35d4780dc91d8e25ba6fa8f62de32a66c9984c`|
|08 documental final|SHA256 `fc69a8e9641f8c9c21c6356300fcd84bb3ad9e4ca62edc4c49ae90cd2832e59c`|
|HEAD|`7816d3328115cf5aa5bcdd0985fffd795b3ae084`, cambios locales previos preservados|
|Build inicial190|`7630c859296fd71dd4607133a461165e1b2d012d5679190652c5e0522bf4fa93`|
|Build final194|`f6ca27baf3813bf8806d449269623e0e9d293e8000dee4cfd83d45dd038cb11c`|
|Chrome188fuentes|`3c1b9ec10f99e695122fbae37451bd0e0462ae601a1f1cc8deca910035b32af3`,final2/cadena-final estables e idénticos por archivo|
|Herramientas|Python3.12.10,Django5.2.18,SQLite3.49.1,Chrome157.0.8103.78,Playwright1.65.1|
|Navegador|13/11/2026 Lima23:15:03–23:15:24;23+44checkpoints,17+14capturas,1280×900,3contextos/roles|
|Regresión final|Lima23:15:00–23:16:23;584/584 en80.237s,fuentes estables|
|Aislamiento|SQLite temporal/memoria,datos ficticios,HTTPWSGIloopback,CSRF y middleware. Sin migrar/abrir base operativa ni desplegar|

[Manifiesto inicial](evidencias/14-G-20261113/build-antes.json) · [Producto anterior completo](evidencias/14-G-20261113/producto-antes.zip) · [Planificación anterior](evidencias/14-G-20261113/planificacion-antes.zip) · [Manifiesto final](evidencias/14-G-20261113/build-final.json) · [Validación final](evidencias/14-G-20261113/validacion-final.json).

### Inventario y trazabilidad

[Inventario detallado](soporte/14-G-inventario.md): HU-INV-01b/2CA y DOC-03AI/4criterios principales; INV-04/CA02 y DEC-05-LOTE-ESPACIOS/C01 como dependencias, ocho criterios total. Siete rutas específicas y11familias de campos/salidas; rutas de roles/POS/caja de la cadena tienen denominador propio. [Matriz exacta](evidencias/14-G-20261113/criterios-final.json). Las74HU/287criterios/112casos escritos de08 se conservan; escribir un caso no acredita ejecutarlo.

| Criterio | Esperado/observado y evidencia nueva | Clasificación final |
|---|---|---|
|HU-INV-01b/CA01|Primera entrada20@4.5000;otra entrega25@5.2000,referencias distintas,reintento sin duplicar. Chrome02/04/08 ytest1|PARCIAL por alcance concurrente/operativo; alta prioridad|
|HU-INV-01b/CA02|Persistencia4decimales,presentación2,costo venta5.2000 y promedio conservado tras salida;captura4.50 deR1 permanece|CUMPLE en muestra; costo histórico operativo no regularizado|
|DOC-03AI/C01|UUID/correlativo/cabecera/líneas/lotes/costo/autor se confirman juntos;R1/R2|CUMPLE en muestraSQLite|
|DOC-03AI/C02|Igualclave/actor/contenido recupera misma recepción;orden/espacios/costo equivalentes;divergencia uotroactor rechaza|CUMPLE en muestra secuencial; HTTP y servicio|
|DOC-03AI/C03|Mismo loteC,mismafecha y nuevaUUID produceR2,otra cantidad/costo/proveedor. Venta conserva ambos orígenes|PARCIAL: dosconexionesPG pendientes15|
|DOC-03AI/C04|Cantidad0/UUID/fecha/precisión/duplicado/estado rechazan sin mutar;correcciónusa mismaUUID;cincofallospostwrite revierten25tablas|CUMPLE en muestra de excepciones;caída real pendiente|
|INV-04/CA02,dependencia|Consulta enlazaR1/R2,autor/proveedororiginal oausencia;legacyincompleto rotulado|CUMPLE en muestra; restoKardex pendiente|
|DEC-05-ESPACIOS/C01,dependencia|`ab  12`≡`AB 12`,`AB12`distinto;duplicadointernorechaza;legacycompara sin reescribir|CUMPLE en muestra; colisiones operativas no diagnosticadas|

SeisCUMPLE en muestra ydosPARCIAL. NingunaHU completa se cierra. Planificación→servidor/persistencia conecta RN01/03/14/19/29,identidadUUID,FEFO,costos y fotografía. Comportamiento→planificación vincula nueva constancia,referencias,avisos de ausencia y selección de procedencia aDOC03AI/INV04. No se incorpora un extra comercial sin respaldo. Cada texto/controlnuevo está inventariado; límites y estados no ejercitados conservan cobertura anterior identificada.

### Hallazgos y efectos entre roles

Chrome previo `antes2/` reprodujo tres problemas: la entrada devolvía carga inicial y no una referencia propia; el reenvío igual era error de lote, mientras la mismaUUID con lote/cantidad distintos creaba otra entrada; una segunda entrega real deC se rechazaba. Además, renombrar proveedor/autor cambiaba el documento. Físico20/promedio4.5000 ya era correcto por14-E; no se atribuye como corrección14-G.

Se implementaron StockReceipt/Line/Counter;UUIDHTTP,huella ordenada,correlativo global y fotografía de ingreso. La cantidad histórica queda separada de capacidad/saldo mutable delLot. Se mantiene laFK técnica a carga por compatibilidad, sin inferirrecepciones de ella. Migración no rellena historia ni reescribe filas. Números nuevos normalizan espacios;legado se compara canónicamente sin fusionarlo.

La muestra conectada recibióC10@6 yC5@8;tras abrir100,vendió22×10=220. Asignó10iniciales+10deR1+2deR2;stock3. ALMACENERO identificóR2 para merma1;ADMIN observóstock2,procedencias,venta y merma. VENDEDOR cerró320 exacto. R1 conserva10UND/promediohistórico4.50 aunque cambien maestros y salganunidades. Selección de ajuste/baja y asignaciones enlazan referencias para distinguir igualnúmero/fecha.

La cadena general nueva creó categoría/producto/proveedor porADMIN, cargó3+7@2porALMACENERO,abrió100,cobró14.20(efectivo20/vuelto5.80),dio bajaa1,dejó5 ycerró114.20. Revalidó categoría inactiva/reactivada,vencimiento,causa/cantidadmerma,efectivo insuficiente,roles por navegación yPOST. Las fixtures14D de ese runner identifican el caso reutilizado;fecha/buildson14-G.

### Pruebas y conservación

| Evidencia | Resultado |
|---|---|
|[Chrome antes2](evidencias/14-G-20261113/navegador/antes2/comparaciones.json)|9checkpoints,problemas reproducidos. `antes/` falló por selector del arnés y se conserva|
|[Chrome final2](evidencias/14-G-20261113/navegador/final2/ejecucion.json)|23checkpoints/17capturas,con BD yHTTP;referencias/reintentos/errores/historia/venta/merma/cierre|
|[Cadena general](evidencias/14-G-20261113/navegador/cadena-final/ejecucion.json)|44checkpoints/14capturas,alta de maestros hasta cierre;buildfinalestable|
|[Servidor](evidencias/14-G-20261113/servidor/INFORME.md)|10tests nuevos con variantes. Cincofallos tras escritura,cambio de estado/fecha,roles,migración ynormalización|
|[Regresión final](evidencias/14-G-20261113/servidor/final2/regresion-final.txt)|584/584,80.237s,sin cambios de fuentes;makemigrations--check sin diferencias|
|Corridas intermedias preservadas|572/583→582/583→583/583 con cambio de fuentes→584/584 estable. Focal7/9 por dosfixtures incorrectas→9/9;se añadió décimotest|
|[Validación documental](evidencias/14-G-20261113/validacion-final.json)|08 yvistas,compatibilidaddecriterios/build,enlaces/huellas y alcance sin cierre integral|

Los conjuntos se solapan. La primera regresión detectó pérdida del triggerreceived_at al reconstruirLot enSQLite y exceso de consultas enmovimientos. Se corrigieron ambos, preservando presupuesto de15consultas y protecciónSQL/ORM. Las demás adaptaciones corresponden aUUID/ruta/etiquetas y rechazo por fecha contradictoria exigidos por contrato;las fuentes antiguas se preservaron. [Comandos navegador](evidencias/14-G-20261113/navegador/RESUMEN.md) · [Comandos servidor](evidencias/14-G-20261113/servidor/INFORME.md).

### Decisiones, omisiones y límites

[Disposiciones14-G](soporte/14-G-disposiciones.md) registra fundamento de aceptación,beneficio,riesgo,costo eimpacto. Se eligió cabecera/líneas/contador sobre el monolito existente; no tabla genérica ni eventos de compra futuros. El usuarioyaautorizó correcciones técnicas de integración; el documento no concede autorización nueva.08incorpora concreción y ejecución parcial antes de regenerar07/09/03.02/14/16/21/01/00 ycontinuidad reflejan este corte.

Las nuevas cargas iniciales todavía consultan nombres de maestros;se advierte esa limitación y queda pendiente capturar suhistoria. NingunaFK/fecha prueba el origen antiguo. Las colisiones/regularización de datosoperativos requieren copiaautorizada yhechos delnegocio. Las excepcionesSQLite no acreditan caída real ni bloqueosPG;estosvan a15. El Kardexcarecedesaldo/filtros/paginación y la merma carecedeconstancia propia/snapshotdeautor. Impresión,móvil/accesibilidadintegral,topesoperativos y restantes requisitos conservansupendiente.

### Cursor exacto

**14-H-KARDEX-SALDOS-01, primera pasada.** SeleccionarHU-INV-04/CA01,03,04 yDEC-08-KARDEX-COMPRAS/C01,03. Preparar secuencia conocida con instantes distintos:carga10,recepciónR1+10,R2+5,venta−22,merma−1. Esperar saldo25antesdeventa,3trasventa,2final. Consultar período quecomienza después decarga/R1:apertura20,entradaR2+5,salidas−23,cierre2. Filtrarsoloventasno debe recalcularsaldooocultarquese excluyeronotrosmovimientos; mostrar saldo real,totalfiltrado yperíodo con significado explícito.

Añadir másde25eventos con empate de instante;probar ordenestable,páginas/filtrospreservados,fecha incompleta/invertida,tipo inválido,GETsinmutación yVENDEDOR403sin costos. Para historialincompleto,noinventarsaldo:declarar límite de reconstrucción. Mantener enlaces aR1/R2 y asignaciones; revalidar costo/merma/caja afectados. Despuéscontinuarconstancia demerma yfotografía de carga inicial,ademásdependientespendientes de14.15–17 y segunda pasada mantienen secuencia.
