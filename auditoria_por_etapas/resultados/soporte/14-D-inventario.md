# Inventario y trazabilidad de integración 14-D

Primera pasada, continuación del 13/11/2026 en Lima. Este inventario acompaña ETAPA-14 y conserva los antecedentes 14-A/B/C. La unidad evaluada es el recorrido ADMIN → ALMACENERO → VENDEDOR → ALMACENERO/ADMIN → VENDEDOR y sus variantes expresamente identificadas. Las ramas de código enumeradas conservan estado NO EJECUTADO hasta tener evidencia de su propia condición.

La versión de 08, el build y el resultado final se registran en el informe de etapa y sus manifiestos. La captura estática intermedia conserva hashes por plantilla y su condición de render. Su nombre expresa que fue obtenida mientras se preparaban las correcciones de este lote. El antecedente del descuento se conserva en la reproducción previa. [Informe](../ETAPA-14.md) · [Build anterior](../evidencias/14-D-20261113/build-antes.json) · [Superficie intermedia](../evidencias/14-D-20261113/inventario/superficie-lectura-intermedia.json) · [Reproducción previa de descuentos](../evidencias/14-D-20261113/descuento-antes.txt).

## Fuentes y criterio de clasificación

| Fuente | Papel y vigencia para 14-D |
|---|---|
| 08 | Contrato funcional principal, RN y decisiones aceptadas. Se exige cada criterio aplicable, incluso cuando las pruebas históricas ejercitan una política anterior. |
| 07, 09 y 03 | Vistas derivadas. Los CA se atribuyen a 08. Una fila de prueba histórica aprobada acredita únicamente la aserción y el build de esa ejecución. |
| 01, secciones Objetivo de producto y Release de consolidación | Una caja, tres roles exclusivos, alcance actual y puertas de aceptación. |
| 02, secciones de arquitectura, integridad, autorización, consultas, transacciones y NFR | Validación en servicios, transacciones, RN-29, exclusión de vencidos, UTC/Lima, ausencia de autorización fundada en campos del navegador. La propia sección de integridad reconoce asignaciones y snapshots aún pendientes. |
| 14, Preparación y Definition of Done | Exige navegador, servidor, persistencia, rechazo sin mutación y evidencia apropiada de concurrencia. Su estado previo «siguiente etapa14, no ejecutada» quedó desfasado respecto de 14-A/B/C y requiere conciliación documental. |
| 16 | Encargos vigentes. DOC-03AH/AI, DEC-11-MODELO, DEC-11-DESCUENTOS, RN-05, DEC-08-KARDEX, DEC-12-PERMISOS, DEC-12-ORDEN, CT-ROLLBACK y DEC-11-TOPE cubren dependencias cruzadas. El tamaño histórico de 67 tareas/216 horas tiene procedencia histórica. |
| CONTROL_SPRINTS | Seguimiento y referencias. Su estado documental no demuestra ejecución de este recorrido. |
| 21, Brechas prioritarias | Advierte valoración, recepción propia, asignaciones, descuentos, causa real de baja, constancia y Kardex incompletos. Un recorrido normal puede terminar conservando esas brechas. |
| XLSX | PLANIFICACION_SCRUM_R1PMV.xlsx ausente en raíz y búsqueda de dos niveles. El antecedente 13 también registra su ausencia. No se utilizó como fuente. |
| Código y plantillas | Identifican la superficie, mensajes y efectos candidatos. La cobertura dinámica se atribuye a los artefactos de navegador/servidor de esta pasada. |

Se leyeron completos PROTOCOLO_COMUN y CONTINUIDAD_Y_SEGUNDA_PASADA. No se localizó AGENTS.md dentro del workspace. Fuentes de alcance y diseño consultadas. [01](../../../01_Proyecto_y_Releases.md) · [02](../../../02_Diseno_Tecnico_R1_PMV.md) · [03](../../../03_Matriz_de_Trazabilidad_y_Pruebas.md) · [07](../../../07_Reglas_de_Negocio.md) · [08](../../../08_Historias_de_Usuario.md) · [09](../../../09_Product_Backlog.md) · [14](../../../14_Sprint_Planning.md) · [16](../../../16_Task_Breakdown.md) · [21](../../../21_Alcance_Actual_y_Diferencias.md) · [Control](../../../r1-pmv/CONTROL_SPRINTS.md).

## Correcciones de atribución del antecedente

| Referencia 14-A | Atribución vigente | Consecuencia |
|---|---|---|
| Alta categoría a HU-CAT-01 | HU-CAT-02/CA-01..03 | CAT-01 acredita la lista. El POST de alta se traza a CAT-02. |
| Alta producto a HU-PROD-01 | HU-PROD-02/CA-01..05 | PROD-01 acredita la consulta. El POST de alta se traza a PROD-02. |
| Movimientos a HU-INV-06 | HU-INV-04/CA-01..04 | INV-06 es historial de ajustes futuro. El comentario de inventory/urls.py que usa HU-INV-06 tampoco sustituye 08. |
| FEFO a RN-05 | RN-19, RN-03, HU-VEN-01c/CA-03 | RN-05 regula causas de merma. FEFO exige además fecha, instante de ingreso e ID. |
| RN-CAJA-01, RN-TURNO, RN-BORRADOR, RN-CIERRE, RN-IDEM, RN-VENCIDO | RN-10, RN-30, RN-25, RN-03 | Los nombres usados en el informe anterior describen temas, pero carecen de ID normativo en 08. |
| 19 HU verificadas y cero incompatibilidades | Muestra de aserciones servidor del corte anterior | La ejecución parcial no levanta los CA suplementarios pendientes de 08 ni aprueba la superficie visual. |
| Navegador real opcional | PROTOCOLO_COMUN §2 y CT-COHERENCIA-UI/C-04 | Este lote aporta interacción real y persistencia. La evidencia HTML previa se conserva como prueba de render de servidor. |

## Inventario de historias y criterios

Las 23 HU de esta tabla están seleccionadas en 08. Cada rango enumera todos los CA base de esa HU y cada fila delimita el subconjunto que participa en 14-D. Su estado al levantar el inventario es NO EJECUTADO en 14-D, salvo las discrepancias de inspección indicadas. La tabla de revalidación al final registra el resultado disponible por caso. Ninguna fila declara finalizada una HU completa.

| HU y CA base de 08 | Tramo y criterio sometido a contraste | Estado inicial y resto pendiente | Antecedente detallado |
|---|---|---|---|
| AUTH-01, CA-01..04 | Ingreso de tres cuentas. Acceso denegado por rol y peticiones directas | CA-01/04 a revalidar. CA-02/03 se mantienen heredados salvo variante explícita nueva | [01](../ETAPA-01.md) |
| AUTH-03, CA-01..03 | Cambiar sesión conserva turno y descarta preparación según confirmación | NO EJECUTADO en la secuencia con contextos separados. Atrás y cancelación quedan pendientes | [02](../ETAPA-02.md) |
| CAT-01, CA-01..02 | Lista usada para crear y cambiar estado de categoría | Lista poblada a revalidar. Vacío NO EJECUTADO | [03](../ETAPA-03.md#1-alcance-fuentes-e-inventario) |
| CAT-02, CA-01..03 | Alta normalizada, repetición y vacío | CA-01 a revalidar. Vacío/duplicado solo cuentan cuando se ejecuten | [03](../ETAPA-03.md) |
| PROD-01, CA-01..03 | Catálogo y disponibilidad tras carga/venta/estado | Lista y cifras a revalidar. Búsqueda/fronteras de mínimo según evidencia particular | [03](../ETAPA-03.md) · [07](../ETAPA-07.md#3-inventario-clasificado-vigente-vs-futuro-y-matriz-entre-roles) |
| PROD-02, CA-01..05 | Registro UND con categoría activa, precio/mínimo y cero stock | Alta nominal a revalidar. Fronteras, equivalencias GTIN y duplicado NO EJECUTADO en navegador salvo evidencia expresa | [03](../ETAPA-03.md) |
| PROD-03, CA-01..02 | Botón y diálogo «Escanear código» accesibles al registrar | NO EXAMINADO dinámicamente en 14-D. Se inventaría porque pertenece a la pantalla. Lector físico pendiente | [03 y anexos](../ETAPA-03.md) |
| PROD-05, CA-01..03 | Inactivar/activar producto afecta oferta y conserva historia | NO EJECUTADO salvo variante servidor nueva. Estado de categoría se cubre por contrato J-CA, no sustituye estos CA | [03](../ETAPA-03.md) |
| PROD-06, CA-01..03 | Consulta y exclusión de lotes con vencimiento <= hoy Lima | La variante de servidor revalida la frontera de vendibilidad. Orden/filtro/pantalla completa siguen pendientes | [07](../ETAPA-07.md) |
| PROV-01, CA-01..02 | Lista proveedor y selección posterior en carga | Lista poblada a revalidar. Homónimos/búsqueda NO EJECUTADO en navegador salvo evidencia particular | [04 §3.3](../ETAPA-04.md#33-contrato-detallado-de-campos-filtros-y-acciones) |
| PROV-02, CA-01..03 | Alta proveedor activo y reutilización por almacenero | Datos nominales a revalidar. CA-01 dice «pedidos» aunque el contrato de recepción directa actual y SOL futuro delimitan su uso | [04](../ETAPA-04.md) · [06](../ETAPA-06.md) |
| PROV-04, CA-01..03 | Estado determina nuevas recepciones y preserva historia | NO EJECUTADO salvo variante servidor nueva. No inferirlo desde la mera existencia de proveedor | [04 y continuaciones](../ETAPA-04.md) |
| INV-01a, CA-01..05 | Almacenero confirma carga de dos lotes del producto nuevo con proveedor | Carga nominal, costo ponderado, persistencia y error a revalidar. Concurrencia/carga única completa se mantiene pendiente | [05 §3.3](../ETAPA-05.md#33-contrato-detallado-de-campos-validaciones-mensajes-y-salidas) |
| INV-02, CA-01..04 | Merma por daño luego de venta, exceso y caducidad/robo | CA-01/03 a revalidar. CA-02 INCUMPLE en código inicial por forzar Vencimiento. CA-04 PARCIAL, hay correlativo y fila sin constancia dedicada | [08 §3.1](../ETAPA-08.md#31-pantallas-rutas-campos-acciones-mensajes-y-salidas-en-alcance-vigente) |
| INV-04, CA-01..04 | Administrador compara entradas, venta, merma y stock actual | PARCIAL. Sin saldo por movimiento, filtros ni asignaciones históricas de venta. La lectura nominal no verifica Kardex completo | [08](../ETAPA-08.md) |
| CAJA-01, CA-01..04 | Vendedor abre turno propio con monto inicial y consulta | Apertura nominal y rechazo por rol a revalidar. Carreras y topes completos pendientes | [09 §3.1](../ETAPA-09.md#31-pantallas-rutas-campos-acciones-mensajes-y-salidas-en-alcance-vigente) |
| CAJA-02, CA-01..05 | Cierre exacto con apertura + venta, persistencia y bloqueo posterior | Cierre nominal a revalidar. Faltante/sobrante/repetición/carrera requieren casos propios | [09](../ETAPA-09.md) |
| CAJA-05, CA-01..02 | Historial de turnos propio/global | Inventariado como salida del cierre. NO EJECUTADO salvo consulta nueva expresa. Filtros y turno ajeno mantienen evidencia heredada | [09](../ETAPA-09.md) · [12](../ETAPA-12.md) |
| VEN-01b, CA-01..05 | Producto cargado aparece en POS, cantidad válida crea borrador sin reserva | Nominal, falta turno y estado comercial a revalidar. Quitar/actualizar/descartar completos pendientes | [10 §3.1](../ETAPA-10.md#31-pantallas-rutas-formularios-campos-límites-y-salidas-ejecutadas) |
| VEN-01c, CA-01..06 | Cobro insuficiente y válido, FEFO de dos lotes, efectivo/vuelto y consumo | CA-01/02/03 a revalidar. CA-04 PARCIAL por asignaciones lote pendientes. Idempotencia, snapshots y concurrencia requieren cada variante | [11 §3.1](../ETAPA-11.md#31-pantallas-rutas-formularios-campos-límites-y-salidas-ejecutadas) |
| VEN-02a, CA-01..04 | Constancia conserva correlativo/importes, aviso literal, recarga y lectura ADMIN | Pantalla y recarga a revalidar. Impresión física y cambios de vendedor/caja quedan pendientes | [12 §3.1](../ETAPA-12.md#31-pantallas-rutas-campos-límites-cabeceras-y-salidas-ejecutadas) |
| VEN-05a, CA-01..02 | Ventas del turno accesibles al vendedor | Menú inventariado. NO EJECUTADO salvo consulta expresa. La existencia de una venta no prueba total de la lista | [12](../ETAPA-12.md) |
| VEN-05b, CA-01..03 | ADMIN ve venta y abre constancia | CA-01/03 a revalidar. Filtros CA-02 y propiedad necesitan casos particulares | [12](../ETAPA-12.md) |

Las HU seleccionadas INV-01b, INV-03 y VEN-01a siguen como dependencias o acciones adyacentes, con alcance NO EJECUTADO en el recorrido nominal de 14-D. El ajuste físico y la recepción posterior exigen sus contratos completos cuando se seleccionen para otra ejecución. El bloqueo de puesto a 300 segundos sigue siendo puerta del piloto.

Las acciones futuras CAT-03/04, PROV-03, INV-05/06, SOL-01..05b, CAJA-03/04/06/07, VEN-04 y VEN-06a/b/c/VEN-07 mantienen PREVISTO/FUTURO. Los rótulos o enlaces visibles relacionados se examinan como promesas de UI cuando aparezcan. El panel mínimo usa DEC-07-VENCIDOS-FILTRO y conserva su antecedente 13. HU-DASH/REP/CONF mantienen su alcance futuro.

## Reglas, contratos y tareas que condicionan el recorrido

| ID de 08 | Criterios o regla aplicable | Estado de contraste de 14-D y tarea vinculada |
|---|---|---|
| RN-01 | Una carga inicial por producto y recepción posterior | Nominal a revalidar. DOC-03AI-01 cubre identidad de recepción posterior pendiente |
| RN-03 | Vencimiento <= hoy Lima bloquea venta | Frontera temporal y caducidad a revalidar en servidor |
| RN-04/05/20 | Causa y detalle de baja, cantidad, autor | Corrección acotada a causa real en este lote. Constancia continúa en RN-05/C-03 |
| RN-06 | Alerta de mínimo | Solo cifras de fixture. Fronteras completas quedan pendientes |
| RN-07/29 | Venta propia/global y rol exclusivo | Tres cuentas separadas y denegaciones. DEC-12-PERMISOS |
| RN-10/30 | Turno único, borrador y cierre | Apertura/cobro/cierre secuenciales. Concurrencia queda en CT-ROLLBACK/SEC-15-CONC-02 |
| RN-14/28 | Promedio sobre físico y costo histórico de salida | PARCIAL heredado y confirmado por inspección. DOC-03AH-01/C-01..04 pendiente, incluso si los lotes nominales tienen el mismo costo |
| RN-19 | FEFO fecha → ingreso → ID | Se puede revalidar elección por dos fechas. Empates y concurrencia necesitan caso propio |
| RN-25 | Venta única, atómica y trazable | Persistencia nominal/rechazos a revalidar. Asignaciones aún faltan. DEC-11-MODELO/C-01..04 |
| RN-26/27 | Constancia interna y aritmética | Revalidación nominal. Fotos históricas vendedor/caja y orden requieren DEC-12-ORDEN |
| PROP-E00-HU-02 | J-CA1..4 de ciclo categoría | Revisar/confirmar/activar/desactivar mientras hay borrador. ABA de versión y rol ajeno completo requieren casos adicionales |
| DEC-05-LOTE-ESPACIOS | C-01..03 | Límites lote, integridad y normalización. `Lot.normalize_number` retira extremos y convierte mayúsculas, conserva espacios interiores múltiples frente a C-01. Queda INCUMPLE por inspección hasta reproducción nueva |
| DEC-04-RUC-VALIDACION | C-01..03 | RUC de formato y destino explícito de estado. Alta nominal no prueba omisión/alteración de estado |
| DEC-11-DESCUENTOS-ALCANCE | C-01..03 | INCUMPLE al inicio. Se retira entrada de descuento y se exige cero/ausencia para nuevo cobro. Reintento histórico con descuento conserva contrato anterior |
| DEC-12-PERMISOS-HISTORIAL-Y-MENU | C-01..03 | Menú por rol, propiedad, sin costos en constancia. Matriz nueva de muestras mantiene casos no cubiertos |
| RN-05 contrato | C-01..04 | C-01 se corrige por causa de robo vencido. C-02 ajuste lote nuevo y C-03 constancia dedicada continúan pendientes. C-04 parcial por reintento, concurrencia PG pendiente |
| DEC-08-KARDEX-COMPRAS | C-01..03 | PARCIAL. Faltan saldos, filtros, paginación estable y lotes de venta. No atribuir CA de saldo a verificar solo stock actual |
| DEC-11-TOPE-EFECTIVO-FORM | C-01..03 | Límite de cierre actual 9 999 999.99 frente a capacidad acumulada 999 999 999 999.99 del contrato. Pendiente. El cierre pequeño no lo aprueba |
| DEC-12-ORDEN-LINEAS-RECIBO | C-01..04 | Una línea no demuestra orden estable multiartículo. GET de preparación/precio actualizado conserva trabajo pendiente |
| CT-COHERENCIA-UI | C-01..04 | Inventario literal, rol, ruta, condición y efectos. Solo se verifican variantes con pasos/evidencias. Cobertura fuente y cobertura dinámica se cuentan por separado |

El mapa contiene 16 RN normativas distintas. Las tablas incluyen contratos suplementarios y tareas ya existentes para impedir duplicación de backlog. DOC-03AH, DOC-03AI, DEC-11-MODELO, DEC-08-KARDEX, DEC-08-CONSTANCIA-MERMA, DEC-12-PERMISOS, DEC-11-TOPE y CT-ROLLBACK mantienen las dependencias de 16.

## Rutas, acciones y permisos

A = ADMIN, M = ALMACENERO, V = VENDEDOR. «Propio» exige además titularidad. «GET/POST» identifica la superficie expuesta y su validación necesaria. Las rutas de respuesta y los alias se cuentan separados para inspección, aunque compartan vista.

| Ruta | Método y actor | Acción y efecto esperado | Traza |
|---|---|---|---|
| / | GET/POST visitante | Formulario e ingreso, crea sesión tras autenticar | AUTH-01 |
| /inicio/ | GET A/M/V | Opciones y cifras propias del rol | DEC-07, RN-29 |
| /salir/ | GET/POST A/M/V | Revisar/confirmar salida. Descarta borrador según RN-30 | AUTH-03 |
| /productos/categorias/ | GET A | Lista/ir a alta/revisar estado | CAT-01, J-CA |
| /productos/categorias/nueva/ | GET/POST A | Crear categoría activa | CAT-02 |
| /productos/categorias/{id}/estado/confirmar/ | GET A | Revisar estado y efecto sin mutación | J-CA1 |
| /productos/categorias/{id}/estado/ | POST A | Destino/version explícitos, cambia elegibilidad | J-CA2/3/4 |
| /productos/ | GET A/M | Catálogo, búsqueda, cifra vigente y alerta | PROD-01 |
| /productos/nuevo/ | GET/POST A | Registrar ficha sin existencias | PROD-02 |
| /productos/codigos/comprobar/ | GET A | Consulta JSON de duplicidad sin reserva | PROD-03 |
| /productos/{id}/registrado/ | GET A | Confirmación de alta y datos | PROD-02/CA-05 |
| /productos/{id}/creado/ | GET A | Alias de confirmación | PROD-02/CA-05 |
| /productos/{id}/editar/ | GET/POST A | Editar ficha, snapshot de versión | PROD-04, adyacente NO EJECUTADO |
| /productos/{id}/disponibilidad/ | POST A | Habilitar/deshabilitar oferta | PROD-05 |
| /productos/vencimientos/ | GET A/M | Fecha, lote y filtro días | PROD-06 |
| /inventario/proveedores/ | GET A/M | Lista, búsqueda y estado | PROV-01 |
| /inventario/proveedores/nuevo/ | GET/POST A | Alta proveedor activo | PROV-02 |
| /inventario/proveedores/{id}/estado/ | POST A | Cambia elegibilidad para recepción | PROV-04 |
| /inventario/carga-inicial/ | GET/POST M | Crear carga única y lotes | INV-01a |
| /inventario/cargas/{id}/ | GET A/M | Consulta carga/entradas, cantidades y costo | INV-01a, DOC-03AI |
| /inventario/carga-inicial/{id}/creada/ | GET A/M | Alias de consulta | INV-01a |
| /inventario/entrada/ | GET/POST M | Recepción posterior | INV-01b, adyacente NO EJECUTADO |
| /inventario/stock/ | GET A/M | Stock físico, vigente, alertas y acceso a movimientos | RN-03/06, DEC-07 |
| /inventario/bajas/nueva/ | GET/POST A/M | Selección lote y retiro por causa | INV-02 |
| /inventario/productos/{id}/movimientos/ | GET A/M | Lista eventos y cantidades | INV-04 |
| /inventario/ajustes/nuevo/ | GET/POST A | Conteo físico | INV-03, adyacente NO EJECUTADO |
| /caja/abrir/ | GET/POST V | Abre turno propio de caja única | CAJA-01 |
| /caja/turnos/{id}/abierto/ | GET V propio | Consulta apertura/estado actual | CAJA-01/02 |
| /ventas/ | GET/POST V | Busca y agrega preparación | VEN-01b |
| /ventas/lineas/{id}/ | POST V propio | Actualiza cantidad | VEN-01b, NO EJECUTADO nominal |
| /ventas/lineas/{id}/quitar/ | POST V propio | Quita y descarta al vaciar | VEN-01b, NO EJECUTADO nominal |
| /ventas/descartar/ | POST V propio | Descarta sin stock/caja | VEN-01b, NO EJECUTADO nominal |
| /ventas/cobrar/ | GET/POST V propio | Revisa y confirma cobro | VEN-01c |
| /ventas/constancia/{id}/ | GET A/V propio | Constancia interna, datos persistidos | VEN-02a |
| /ventas/historial/turno/ | GET V propio | Ventas y totales del turno | VEN-05a |
| /ventas/historial/ | GET A/V propio | Lista y filtros, abre detalle | VEN-05b |
| /caja/cerrar/ | GET/POST V propio | Declara contado y cierra | CAJA-02 |
| /caja/turnos/{id}/cerrado/ | GET A/V propio | Acta del cierre | CAJA-02/05 |
| /caja/turnos/ | GET A/V propio | Historial y filtros | CAJA-05 |

Son 39 patrones inventariados, incluidos tres adyacentes de edición/recepción/ajuste y dos alias. La matriz expresa el permiso esperado por código/08. Cada petición real nueva se identifica en http.json y en las variantes de servidor. Las superficies de empleados, portal técnico, error404/500 y todos sus estados quedan fuera del lote de integración actual. La respuesta403 sí se incluye por su efecto y mensaje.

## Campos, límites, mensajes y persistencia

«Vacío» describe el valor inicial al abrir un alta. El inventario de campos se completa con los controles renderizados capturados por paso en navegador. Los límites de fuente y sus mensajes requieren sus propias fronteras de prueba.

| Campo y etiqueta literal | Propósito, inicial y obligatoriedad | Tipo, normalización y límites actuales | Error/rechazo y persistencia | Requisito |
|---|---|---|---|---|
| Login email, «Correo de trabajo» | Identificar cuenta, vacío, requerido | EmailField, recorta extremos. El formulario de login usa límite Django por defecto | Error formato o «Correo o contraseña incorrectos». Sesión solo al autenticar | AUTH-01 |
| Login password, «Contraseña» | Autenticar, vacío, requerido | Texto password, strip=False | Mensaje general. El valor no se conserva en evidencia ni se presenta de nuevo | AUTH-01 |
| Category.name, «Nombre de la categoría» | Alta, vacío, requerido | 1..120, espacios normalizados, unicidad casefold | «El nombre es obligatorio», «La categoría ya existe», exige letras/números. Category activa | CAT-02 |
| Product.name, «Nombre del producto» | Nombre comercial, vacío, requerido | 1..160, colapsa espacios y clave de búsqueda normalizada única | «Ya existe un producto registrado con este nombre.» Product.name/search_name | PROD-02 |
| Product.barcode_type, «Tipo de código» | Elegir INTERNAL/GTIN, «Seleccione el tipo», requerido | Choice. GTIN y clave interna tienen políticas distintas | Elección inválida/obligatoria. Clasificación persistida | PROD-02/03 |
| Product.barcode, «Código de barras» | Identificador, vacío, requerido | Hasta64. Interno letras/números/espacios/guiones. GTIN12/13 o14 con cero inicial y dígito verificado | Duplicidad conserva reserva. Product y ProductBarcodeKey | PROD-02/03 |
| Product.category, «Categoría» | Relación, sin selección, requerido | UUID activo del queryset | «Seleccione una categoría válida de la lista.» FK protegida | PROD-02 |
| Product.unit, «Unidad de medida» | Presentación, UND | Choice UND en alcance | Otra unidad rechazada. Control de vencimiento forzado | PROD-02 |
| Product.sale_price, «Precio final con IGV (S/)» | Precio final, vacío, requerido | Decimal2, 0.01..9999999.99. Sin notación científica | Error precisión/rango. Product.sale_price | PROD-02, RN-27 |
| Product.minimum_stock, «Existencia mínima» | Alerta, 10 por defecto, opcional al alta | Entero0..999999. Vacío se normaliza a10 | Error rango/entero. Product.minimum_stock | PROD-02/CA-04, RN-06 |
| «Código leído» del diálogo | Captura revisada, vacío | Texto máximo64, consulta duplicado antes de copiar | «El código de barras ya está registrado», «Sin duplicados en esta consulta. Se volverá a comprobar al guardar.» No guarda ficha | PROD-03 |
| Supplier.name, «Nombre comercial» | Alta, vacío, requerido | Hasta160, espacios normalizados, alfanumérico requerido. Homónimos admitidos | «El nombre del proveedor es obligatorio.» Supplier.name | PROV-02 |
| Supplier.ruc, «RUC» | Identidad, vacío, requerido | Exactamente11 dígitos ASCII, extremos recortados, único | «El RUC debe contener exactamente 11 dígitos numéricos.» / «El RUC ya está registrado.» | PROV-02, DEC-04 |
| Supplier.phone, «Teléfono» | Contacto ficticio, vacío, opcional | Hasta20, caracteres números/espacios/+/-/paréntesis y al menos un dígito | Error de formato. Supplier.phone | PROV-02 |
| Carga product, «Producto» | Selección ficha nueva, «Seleccione un producto», requerido | UUID, activo/categoría activa, sin carga, controla vencimiento | «Este producto ya tiene una carga inicial registrada o no está disponible.» FK en carga/lotes | INV-01a |
| Carga supplier, «Proveedor (opcional)» | Origen comercial, «Sin proveedor asignado», opcional | UUID de proveedor activo o vacío | Selector preserva proveedor rechazado. «El proveedor … está inactivo.» Sin lotes ante rechazo | INV-01a, PROV-04, DOC-03AB |
| Lote number, «Número de lote» | Identidad comercial, vacío, requerido en fila usada | 1..64, extremos y uppercase. Espacios internos aún divergen de DEC-05/C-01 | Vacío/NUL/duplicado normalizado rechazados. Lot.number/number_normalized | INV-01a/CA-02 |
| Lote quantity, «Cantidad» | Unidades recibidas, vacío, requerido | Entero1..999999 ASCII, step1 | Error campo. Lot.initial_quantity/available_quantity | INV-01a |
| Lote unit_cost, «Costo unitario (S/)» | Valorar carga, vacío, requerido | Decimal4 0.0001..9999999.9999, ASCII, sin exponente | Error precisión/rango. Lot.unit_cost y promedio producto | INV-01a, RN-14 |
| Lote expiration_date, «Vencimiento» | Elegibilidad, vacío, requerido | Fecha ISO, >hoy Lima y hasta20años | «El vencimiento debe ser posterior a hoy en Lima.» Sin carga parcial | INV-01a, RN-03 |
| opening_amount, «Monto inicial (S/)» | Efectivo apertura, vacío placeholder0.00, requerido | Decimal2 0..9999999.99 ASCII, sin exponente | Error campo, conflicto turno. CashShift.opening_amount | CAJA-01 |
| POS query, «Buscar producto» | Hallar por nombre/código, vacío, opcional | Texto hasta160, consulta solo elegibles | Cero resultados o validación. Sin mutación comercial | VEN-01b |
| POS product_id, oculto | Producto agregado, UUID generado por consulta | UUID revalidado | Producto inexistente/inactivo/no vendible rechaza | VEN-01b |
| POS quantity, «Cantidad» | Agregar/actualizar unidades, entero positivo | 1..999999, sin signo+, ASCII y <=stock vendible | «Ingrese una cantidad entera mayor que cero usando dígitos ASCII.» Borrador sin reserva | VEN-01b |
| cash_received, «Efectivo recibido (S/)» | Monto recibido, vacío, requerido | Decimal2, 0.01..9999999.99 y >=total | Insuficiente/precisión/rango sin venta, stock ni correlativo. Sale.cash_received y change_given | VEN-01c |
| discount_amount, «Descuento (S/) - opcional» inicial | Campo presente en build anterior | Decimal2 opcional, >=0. Contradice contrato de nuevos cobros | Estado inicial INCUMPLE. El build final retira control y exige cero/ausente. Los registros históricos conservan descuento | DEC-11-DESCUENTOS |
| Baja lot_id, oculto | Lote escogido por enlace ?lote=UUID | UUID existente con disponible>0 para selector | Error/404 para desconocido. La URL no autoriza el retiro | INV-02 |
| Baja quantity, «Cantidad a dar de baja» | Retiro, vacío, requerido | Entero1..999999 ASCII, <=disponible | «La cantidad supera las existencias disponibles del lote.» StockWriteOff.quantity y saldo lote | INV-02/CA-01 |
| Baja reason, «Motivo» | Causa real, selector requerido | VENCIMIENTO, DAÑO, ROBO | Antes forzaba Vencimiento en lote vencido. Final debe aceptar ROBO con detalle y rechazar DAÑO vencido | INV-02/CA-02, RN-05 |
| Baja notes, «Detalle (obligatorio para Daño y Robo)» | Explicación, vacío, requerido según causa | Texto recortado, sin NUL, sin máximo explícito de formulario | «Detalle obligatorio para Daño o rotura y Robo o faltante.» Se conserva en baja | INV-02/CA-03, RN-20 |
| counted_amount, «Monto contado (S/)» | Arqueo, vacío, requerido | Form Decimal2 0..9999999.99. Capacidad esperada normativa de acumulado mayor | Error no cierra. CashShiftClose contado/esperado/diferencia | CAJA-02, DEC-11-TOPE |
| Estados is_active, state_version ocultos | Destino y revisión categoría/producto/proveedor | Booleano explícito y versión de categoría. Servidor reautoriza | Categoría antigua muestra «La categoría cambió desde que abrió esta pantalla. Revise el estado actual antes de continuar.» | J-CA, PROD-05, PROV-04 |
| idempotency_key, expected_subtotal, draft_signature ocultos | Identidad/revisión de cobro | UUID/Decimal2/firma. Nunca autoridad para precio o rol | Reintento distinto rechaza. Una venta por clave | RN-25, VEN-01c |
| Baja idempotency_key oculto | Evitar repetir baja | UUID ligado a payload/sesión | «Esta baja ya fue registrada anteriormente.» | RN-05/C-04 |
| management_form lots-* oculto | Estructura de filas de carga | TOTAL/INITIAL/MIN/MAX, formset min1 y extra3 | Error formset rechaza entero. No es cantidad de negocio | INV-01a, NFR-01 |
| Consultas q/dias/fecha/fecha_desde/fecha_hasta/vendedor/turno/correlativo | Búsqueda y filtros | Texto, días ASCII1..3650, fechas ISO y UUID según pantalla | Error fecha/rango conserva mensaje, restringe por rol. Sin mutación comercial | PROD-01/06, PROV-01, CAJA-05, VEN-05b |

La tabla agrupa 36 entradas de campo o familia homogénea. Los controles HTML concretos se cuentan en la captura por paso, por eso una fila de lotes repetida y sus parámetros ocultos no representan 36 campos distintos de modelo.

## Textos, acciones y salidas por estado

El anexo JSON conserva cada literal o variable de plantilla con archivo, línea, ruta, rol y rama. Los mensajes Python extraídos incluyen fragmentos de validación y formatos internos, identificados como candidatos. Las 30 plantillas inventariadas se enlazan al criterio de pantalla y CT-COHERENCIA-UI. Las decisiones dinámicas adicionales del lector y del cálculo de cobro requieren su evidencia propia.

| Pantalla/estado | Literales o variables operativas que se contrastan | Efecto esperado y traza |
|---|---|---|
| Marco autenticado | «Inicio», «Productos», «Registrar producto», «Categorías», «Proveedores», «Ver inventario y alertas», «Vencimientos de lotes», «Ajuste físico», «Empleados», «Historial de turnos», «Historial de ventas», «Mis ventas del turno», «Cerrar sesión» según rol | RN-29/DEC-12. Link, rol y vista deben corresponder. Las opciones ajenas al recorrido permanecen inventariadas |
| Categoría alta/lista | «Nueva categoría», «Nombre de la categoría», «Guardar», «Cancelar», «Categoría «{nombre}» creada correctamente.», «Nombre», «Estado», «Acciones» | CAT-01/02. Éxito exige fila activa y disponible al registrar producto |
| Categoría revisión | «Confirmar desactivación», «Confirmar activación», nombre/estado/efecto, aviso de cambio de versión | J-CA1..4. GET/cancelar sin mutación, POST afecta oferta y conserva historia |
| Producto alta | «Registrar producto», «Existencias iniciales: 0», «UND», «Incluye IGV», «10 por defecto», «Disponible para venta», «No» | PROD-02. Datos de ficha sin carga ni stock |
| Producto catálogo | «Existencias vigentes (UND)», «Stock mínimo», «Disponibilidad», «Stock bajo», «Inactivo», «Categoría desactivada», «Disponible», «Sin stock vigente», «Editar», «Deshabilitar», «Habilitar» | PROD-01/04/05 y RN-06. El número vigente y la disponibilidad comercial conservan significado distinto |
| Proveedor | «Nuevo proveedor», «Guardar», «Cancelar», «Proveedor «{nombre}» registrado.», «RUC», estado activo/inactivo y botón destino | PROV-01/02/04. Figura para almacenero solo si activo. RUC se limita a validar formato |
| Carga inicial | «Producto», «Proveedor (opcional)», «Sin proveedor asignado», «Lotes recibidos», «Completa una o más filas», «Confirmar existencias» | INV-01a. Selección activa y validación completa antes de commit |
| Carga confirmada | «Existencias confirmadas», «Carga inicial confirmada», «Responsable de carga inicial», fecha, «Existencias físicas», «Costo promedio», tabla lotes | INV-01a. Autor/instante/lotes y suma iguales a BD. «Entradas posteriores de mercadería» queda dependiente de INV-01b/DOC-03AI |
| Apertura | «Monto inicial (S/)», «{caja} está abierta», «Ir a preparar venta», «Turno de {caja} cerrado», «Ver acta de cierre» según estado | CAJA-01/02. Un turno propio, monto original y estado persistido |
| Preparación | «Buscar producto», «Cantidad», precio, cantidad e importe por línea, total/base/IGV, «Última constancia» | VEN-01b/RN-27/30. Borrador sin efecto en existencias/efectivo |
| Cobro antes | «Descuento (S/) - opcional», ayuda «Deja en blanco si no hay descuento. El resumen de la derecha se actualiza automáticamente.» | INCUMPLE DEC-11-DESCUENTOS/C-01 al inicio. Su presencia ofrecía una operación suspendida por planificación |
| Cobro final | «Efectivo recibido (S/)», «Debe ser igual o mayor al total de la venta.», «Confirmar cobro», «Procesando cobro…», total/base/IGV/vuelto estimado | VEN-01c, DEC-11-DESCUENTOS. Confirmación revalida y persiste. Los textos finales exactos están en la captura posterior |
| Constancia | Correlativo V-{8d}, fecha Lima, vendedor/caja, código/nombre/cantidad/precio/importes, efectivo/vuelto, «CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO» | VEN-02a/RN-26/27. Debe recuperar mismo número y valores tras recarga, sin costo de compra |
| Stock tras venta/merma | «Inventario actual», «Stock físico», «Stock vigente», «Mínimo», «Estado», «Ver movimientos», alertas de mínimo/vencido | RN-03/06, DEC-07. Suma física, vigente y disponibilidad coherentes con lote y maestro |
| Baja selección/formulario | «Registrar baja de inventario», «Seleccione el lote a dar de baja:», «Dar de baja», «Lote seleccionado:», «Disponible:», «Vence:», «Confirmar baja», «Cancelar» | INV-02. Verificación de lote/cantidad/motivo/detalle/rol en servidor |
| Baja confirmada/repetida | «Baja {correlativo} registrada correctamente.», «Esta baja ya fue registrada anteriormente.» | INV-02/RN-05. Éxito exige saldo y registro. Constancia dedicada aún pendiente |
| Movimientos | «Stock físico actual: {n} unid. · Stock vigente: {n} unid.», «Movimientos: {producto}», «Fecha», «Tipo», «Detalle», «Cantidad», «Responsable» | INV-04 PARCIAL. Actual no muestra saldo de cada fila |
| Fila de movimiento | «Carga inicial — Lote {n} ({proveedor})», «Venta {V}», «Merma ({motivo}) · {M} — Lote {n}{notas}» | Cantidades/autor contrastables. Venta carece de asignación de lote. Proveedor/nombre vía relación tienen limitación histórica |
| Historial de ventas | «Correlativo», «Fecha exacta», «Desde», «Hasta», «Vendedor», «Turno», «Filtrar», «Limpiar», «Pago», «Descuento (S/)», «Total (S/)», «Efectivo recibido», «Vuelto» | VEN-05b/DEC-12. Descuento histórico sigue siendo salida válida. Filtros completos requieren variantes propias |
| Cierre | «Cerrar y cuadrar caja», «Monto contado (S/)», «Cerrar turno», «El cierre es irreversible. Verifica el efectivo antes de confirmar.» | CAJA-02. Esperado = apertura + total ventas confirmadas, diferencia = contado−esperado |
| Acta | «Turno cerrado correctamente», «Acta de cierre del turno», «Exacto», datos del turno y cierre | CAJA-02/05. Recarga no duplica ni altera |
| Sin turno /403 | «Requiere turno abierto» y página de acceso denegado con regreso seguro | AUTH-01/CA-04, VEN-01b/CA-01, RN-29. Sin datos ajenos ni mutación comercial |

## Componentes internos y efectos entre roles

| Necesidad | Componente actual | Persistencia y comprobación necesaria |
|---|---|---|
| Autenticar y delimitar rol | identity.services, roles_required, sesión Django | Cuenta/rol activo revalidado, cookie y POST. Login genera datos técnicos excluidos del hash de negocio cuando se compara un rechazo |
| Maestro nuevo disponible para almacenero | create_category, register_canned_product, create_supplier | Category, Product, ProductBarcodeKey, Supplier. Debe seguir con cero lotes hasta carga |
| Existencias para vendedor | confirm_initial_load, LotInputFormSet | InitialInventoryLoad y Lot, promedio producto, responsable/proveedor. La primera búsqueda POS recupera stock vendible |
| Preparación privada | add_product_to_draft, SaleDraft/Line | Solo preparación. Hash de stock/caja estable antes del cobro |
| Venta FEFO | checkout_sale, CashShift, SaleCounter, Sale/Line | Un cobro confirma número/importes y reduce lote. Asignaciones históricas por lote siguen pendientes de DEC-11-MODELO |
| Baja tras cobro | write_off_stock, StockWriteOff | Disponible restante y causa/autor/correlativo. Sin alterar venta/caja. Promedio móvil conserva brecha DOC-03AH |
| Consulta cruzada ADMIN | product_movements, sales_history, sales_receipt | GET muestra resultado de los otros actores. Cambios futuros en maestros no deben rehacer snapshots requeridos |
| Cierre vendedor | close_cash_shift, CashShiftClose | Turno CLOSED y un acta, esperado por total neto de cobros y diferencia exacta. Preparar tras cierre falla sin mutación |

## Recomendaciones y omisiones legítimas

| Propuesta o encargo existente | Beneficio | Riesgo y alternativa | Costo relativo e impacto |
|---|---|---|---|
| Completar DEC-11-MODELO-AUDITORIA-VENTAS y DEC-08-KARDEX-COMPRAS | Reconstruir qué lote salió y conciliar merma/venta | La inferencia FEFO a posteriori puede adjudicar lote equivocado. Conservar explícito «origen no disponible» para legado es la alternativa admitida | Medio/alto. Esquema, diagnóstico legacy, servicio de cobro y consultas, regresión de INV/VEN |
| Completar RN-05/C-03 y DEC-08-CONSTANCIA-MERMA | Administrador y almacenero comparten prueba inmutable del retiro | Correlativo en mensaje y fila no basta para consulta dedicada. Alternativa mínima, vista de detalle imprimible de baja existente con snapshots requeridos | Medio. Datos, permisos y presentación. No crea una HU duplicada |
| DOC-03AH-01 y prueba con costos distintos/vencidos | Evitar que una merma altere artificialmente el costo de las unidades restantes | La fixture con mismo costo puede ocultar reponderación incorrecta. Alternativa, mantener brecha y bloquear cierre de valoración | Medio/alto. Diagnóstico de datos, entradas, salidas y snapshots. Ya aceptado con evidencia pendiente |
| Completar matriz de negativas por transición | Evitar que acciones permitidas al actor previo rompan el paso del siguiente | Las capturas nominales omiten revocación de cuenta/estado concurrente. Extender casos existentes aporta evidencia | Bajo/medio. Pruebas de integración y PG cuando exista competencia. RN-29, CT-ROLLBACK y CP-VISIBLE |
| Resolver etiquetas heredadas HU-INV-06 y RN temáticas | Evitar aprobar una HU futura por una vista actual | Cambiar el requisito para conservar un comentario reproduce el error. Actualizar comentario/documentación mantiene su procedencia | Bajo. Mapa documental y pruebas, sin cambio funcional |
| Investigar política de existencias solo vencidas al arranque | Permitir registrar inventario real sin fabricar lote vigente | Requiere procedimiento de apertura y valoración fiable. Alternativas de ajuste inicial documentado o carga separada de no vendibles siguen sujetas a decisión de negocio | Medio. RN-05 ya registra la investigación, no hay nuevo permiso de recepción vencida |

La autoría del inventario no acepta nuevas políticas. Descuento suspendido y causa real de merma ya tienen contratos aceptados en 08. La ejecución de 14-D puede verificar una corrección de esos contratos sin reabrir una decisión comercial. Los encargos amplios conservan su estado y prioridad.

## Registro de revalidación de este lote

El inventario final tiene 23 HU principales y 80 CA base, extraídos por ID desde 08, 16 RN, 39 patrones de ruta y 36 filas de campo o familia homogénea. La matriz individual mantiene 49 CA PARCIAL, 2 INCUMPLE y 29 NO EJECUTADO en este sublote. Hay muestras nuevas vinculadas a 50 de los 80 CA, pero la cobertura completa de condiciones de cada CA continúa delimitada por el texto de la fila. INV-04/CA-04 incumple por inspección de vista y plantilla y carece de ejecución particular de filtros porque no existe esa superficie. Las dos fuentes de evidencia son servidor y navegador del build de 14-D. [Matriz individual de 80 CA](../evidencias/14-D-20261113/inventario/criterios-base.json).

El extractor final produjo 30 plantillas con 1 320 fragmentos de literal, variable, control o atributo y 313 cadenas Python candidatas. Estos conteos describen la superficie de fuente. Una misma frase puede ocupar varios fragmentos, y las cadenas Python incluyen formatos técnicos. Cada rama conserva su requisito de pantalla y necesita su propia evidencia dinámica. Los 44 pasos del recorrido3 registran el texto realmente visible y los controles por estado. [Superficie final](../evidencias/14-D-20261113/inventario/superficie-final.json) · [Ejecución real](../evidencias/14-D-20261113/navegador/recorrido3/ejecucion.json) · [Peticiones HTTP](../evidencias/14-D-20261113/navegador/recorrido3/http.json).

| Bloque revalidado | Evidencia nueva | Resultado y límite |
|---|---|---|
| Tres roles y denegación | B01/02/03/04/05b/11/12b/15/20b, servidor S01..05 | CUMPLE para las rutas y métodos ejecutados, con denegación y huella comercial estable. El mapa completo de autorización sigue con sus casos pendientes |
| Altas ADMIN y carga ALMACENERO | B05..14, incluidos B05b/12b/13 | Categoría/producto/proveedor creados desde UI. Carga de dos lotes3+7, rechazo de vencimiento y acceso indebido sin cambios. Contrasta CA nominales y entrega efectiva entre roles |
| Borrador y cambio categoría | B18..24, S08..10 | La categoría desactivada bloquea un cobro ya revisado. Reactivación permite continuar. Rechazo conserva tablas. La variante de estado de producto se ejecuta en servidor |
| Cobro y FEFO | B25..29, S06/13/17 | Total14.20, recibido20.00, vuelto5.80. Salida3+1, quedan6. Recarga conserva V-00000001. Caso de servidor que vence hoy rechaza. Asignaciones históricas por lote continúan pendientes |
| Merma | B30/30b/31/32, S11..16 | Exceso y causa incompatible rechazados. Daño de una unidad deja5. Robo explicado de lote vencido pasa tras corrección, sin explicación rechaza. Constancia dedicada y valoración siguen pendientes |
| Contraste ADMIN | B33..36 | Inventario5, movimientos+3/+7/−4/−1, venta y constancia accesibles. Kardex PARCIAL frente a saldos/filtros/atribución de lote |
| Cierre vendedor | B37..40, S07/18 | Esperado114.20, contado114.20, diferencia0 y estado CLOSED. Recarga estable, preparación sin turno bloqueada. La variante servidor rechaza segundo cierre y cierre con borrador |
| Descuento corregido | B20/26/27, suites descuento-despues y regresión final | Control de descuento retirado. Rechazo de descuento nuevo y reintento histórico cubiertos en las pruebas específicas. El contrato conserva registros históricos y sus importes |

Los pasos B remiten al prefijo de archivo JSON en recorrido3. S remite al campo id de variantes-despues.json. Las ejecuciones previas del runner quedan conservadas como antecedentes. La ejecución3 declara recorrido_completo y build_estable, con 44 pasos guardados. Las 18 variantes de servidor declaran CUMPLE para sus aserciones particulares. [Variantes de servidor](../evidencias/14-D-20261113/servidor/variantes-despues.json) · [Pruebas de descuento](../evidencias/14-D-20261113/descuento-despues.txt) · [Regresión final](../evidencias/14-D-20261113/servidor/regresion-final.txt).

Cursor funcional siguiente, probar una secuencia de costos distintos y vencidos conforme DOC-03AH-01, luego asignaciones de lotes DEC-11-MODELO y Kardex con saldo inicial/final y filtros DEC-08-KARDEX, conservando el legado explícito. La constancia dedicada de merma RN-05/C-03, límites acumulados de cierre y normalización interior de lote siguen pendientes. Los CA y campos con ausencia de ejecución particular mantienen sus estados en la matriz individual.

## Compatibilidad con el cierre documental de 08

La comparación adicional del 13/11/2026 conserva el hash observado por Chrome y el de su actualización documental. El 08 inicial fue `33d2f17067fec3bb30e018ef49b77d87f84adfd9bafe04adf19161cd286e47a4` y el final `e8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847`. Los 80 CA de la matriz conservan texto idéntico, igual que los cuatro criterios suplementarios RN-05 y los tres de DEC-11-DESCUENTOS-ALCANCE. Las 30 plantillas conservan los hashes de superficie-final.json. El delta documental cambia seguimiento, precisa tres variantes independientes de merma y agrega CP-INTEGRACION-ROLES-001. Las capturas de ejecución y los anexos originales mantienen su versión. [Comparación final](../evidencias/14-D-20261113/inventario/compatibilidad-08-final.json) · [Comparación documental intermedia](../evidencias/14-D-20261113/inventario/compatibilidad-08-posterior.json).

| Contrato final | Resultado acotado frente a sus condiciones |
|---|---|
| DEC-11-DESCUENTOS-ALCANCE/C-01 | Revalidado en las muestras de campo ausente/cero y rechazo de positivo/negativo/inválido/múltiple, servidor y formulario. Chrome confirma ausencia del control y total completo. |
| DEC-11-DESCUENTOS-ALCANCE/C-02 | Revalidado en fixture histórica subtotal20/descuento2/total18, consulta y recuperación idempotente por servicio/HTTP, incluidos reintentos después del cierre. |
| DEC-11-DESCUENTOS-ALCANCE/C-03 | Revalidado en precio completo y efectos de caja/IGV. El recorrido Chrome usa14.20 y las pruebas específicas ejercitan sus importes propios. |
| RN-05/C-01 | PARCIAL. Causa de robo vencido y detalle fueron corregidos y revalidados. El costo histórico de salida conserva la dependencia DOC-03AH-01. |
| RN-05/C-02 | NO EJECUTADO en14-D. Ajuste ADMIN con lote nuevo y origen propio queda pendiente. |
| RN-05/C-03 | PARCIAL. Correlativo y registro de merma comprobados. Constancia dedicada inmutable pendiente. |
| RN-05/C-04 | PARCIAL. Rechazos conservan datos en las variantes nuevas. Concurrencia venta/baja/ajuste, doble POST completo y recuperación bajo carrera mantienen prueba propia. |
| CP-INTEGRACION-ROLES-001 | EJECUTADO PARCIAL según08. Recorrido3 y S01..S18 cubren la cadena y variantes declaradas. Los cinco criterios transversales citados en el caso mantienen su alcance completo y sus pendientes. |

El caso nuevo agrega una especificación de prueba sobre HUs y criterios existentes. El denominador de este inventario conserva23HU/80CA y el catálogo completo pasa a112casos escritos. Las verificaciones que acreditan descuento y causa de merma mantienen la cobertura acotada de las disposiciones. [Caso de integración](../../../08_Historias_de_Usuario.md#CP-INTEGRACION-ROLES-001) · [Disposiciones y límites](14-D-disposiciones.md).
