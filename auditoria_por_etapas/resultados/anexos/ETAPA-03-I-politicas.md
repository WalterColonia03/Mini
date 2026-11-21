# Etapa03-I · Máximo y nombres aceptados

**10/11/2026, America/Lima. Sublote implementado y verificado en datos aislados.** El usuario pidió recomendaciones para las dos preguntas pendientes y aceptó con «bien, continua»: máximo técnico999999/predeterminado10 y nombres únicos ignorando mayúsculas y espacios redundantes, distinguiendo marca, contenido o presentación. PROP-03C-LIMITES y PROP-03C-NOMBRE pasan de pendientes a aceptadas; no se deduce aceptación de funcionalidades adicionales.

## Fuentes e inventario previo

Se leyó completo el protocolo y se retomó03-H. [Inventario previo y hashes](../evidencias/03-I-inventario-20261110T165406169875Z.json). Fuentes: HU-PROD-02 CA01/CA04, HU-PROD-04 CA02/CA04, RN06/RN29, adendas vigentes de02/03/09/16/21, conflictos documentados03-C y corrección de fracciones03-H. 01/14/CONTROL_SPRINTS y XLSX mantienen su función histórica; no se cambiaron sprints, puntos ni el libro. Se usó la guía ui-ux-pro-max para ayuda y error junto al campo; no se rediseñaron pantallas.

| Requisito / actor / clasificación inicial | Superficie y salida inventariada | Resultado verificable / prioridad |
|---|---|---|
| PROD02-CA04/RN06, ADMIN; máximo aceptado pendiente de aplicar al servicio | GET/POST `/productos/nuevo/`; ProductRegistrationForm, register_canned_product, Product y base | Entero0..999999; alta vacía/omitida10. H01–04 repetidos, pruebas de servicio y PG-I07. CUMPLE muestra, P2 |
| PROD04-CA02/RN06, ADMIN | GET/POST `/productos/<uuid>/editar/`; ProductEditForm/update_product | Conserva mínimo válido; inválido rechaza sin guardar nombre/código/precio. H07–09, ProductPolicyTests, PG-I07. CUMPLE muestra, P2 |
| PROD02-CA01 / PROP-03C-NOMBRE aceptada, ADMIN | Alta, nombre, ayuda, error; clave search_name | Duplicados de mayúsculas/espacios/NFC rechazados incluso inactivos/otras categorías. I01–03/I06, métodos nuevos, PG-I04/06. CUMPLE muestra, P1 |
| PROD04-CA04 / PROP-03C-NOMBRE aceptada, ADMIN | Edición, búsqueda en catálogo/venta, histórico | Propia ficha admite su nombre; homónimo ajeno rechaza todos los cambios. I04/05/07/08, PG-I05/08. CUMPLE muestra, P1 |
| PROD01/RN29, ALMACENERO | Menú catálogo, filas y mínimo | Consulta seis productos; nombres distintos por presentación, sin acciones de edición. H05/I07. CUMPLE muestra |
| Venta autorizada, VENDEDOR; visitante | Menú Preparar venta; POST directo de alta/edición; GET edición visitante | Sin agregar productos sin stock; roles no autorizados403 y visitante302, sin mutación. H06/H10/H11/I08. CUMPLE muestra; no cierra ventas |
| AUD03I-MIG01, tarea técnica | Migración0005 y datos previos | Conflictos abortan antes de escribir; migración válida conserva campos comerciales. PG-I01/02/03. CUMPLE aislado; uso real PENDIENTE |

Las rutas de confirmación, categoría/estado, código, precio y demás campos mantienen trazabilidad03-A..H. Las seis CA futuras de editar/eliminar categoría y escáner no se convierten en aprobadas por esta decisión.

**Nombre del producto:** texto obligatorio, máximo160 después de normalizar espacios; inicial vacío en alta y nombre actual en edición. Se colapsan separadores entre palabras y se eliminan espacios en extremos; la clave usa casefold/NFC. Mantiene acentos: «Atún» y «Atun» siguen distintos, mientras «Atún» y su representación Unicode compuesta coinciden. La unicidad es global entre activos/inactivos y categorías; nombre propio excluido en edición. Ayuda visible nueva: «Nombre único. Distinga marca, contenido o presentación; se ignoran mayúsculas y espacios redundantes.» Error exacto: «Ya existe un producto registrado con este nombre.». No se fusionan productos de mismo nombre ni se reutiliza su código. Extremos generales160 y caracteres fueron auditados03-C/D; no se afirma probar Unicode exhaustivo en03-I.

**Existencia mínima:** input numérico, paso1, rango0..999999. Alta opcional, inicial10, omisión/vacío10; edición obligatoria, inicial persistido. Error máximo: «Asegúrese de que este valor sea menor o igual a 999999.»; fracciones/texto inválidos mantienen error de entero. El mínimo no crea stock. La ayuda actual ya indicaba el rango; ahora servicio/modelo y CHECK persistente lo hacen cumplir.

## Cambios y pruebas

- **AUD03I-MIN01:** MaxValueValidator en modelo y CHECK `product_minimum_stock_lte_max`. Se conserva el rechazo de fracciones/bool/no finitos de FIX03H-01. Alta/edición y actualización SQL ensayada rechazan1000000.
- **AUD03I-NOM01:** search_name UNIQUE, normalización de espacios compartida entre modelo/búsqueda/formulario. Guardar parcialmente name también actualiza su clave. Servicios recuperan conflictos fuera de un savepoint y los vinculan al campo correcto; otros IntegrityError se propagan. La edición rechazada no modifica ningún campo persistido.
- **AUD03I-MIG01:** `catalog.0005_product_name_and_minimum_policy` examina todas las filas antes de recalcular claves. Ante nombre vacío, colisión o mínimo fuera del rango, aborta con identificación de filas para resolución explícita. No recorta, elimina, fusiona ni renombra automáticamente. En éxito conserva nombres visibles e identidad/referencias; la normalización del nombre visible ocurre al editar después.
- **AUD03I-DOC01:** HU02-CA01/CA04, HU04-CA04 y RN06 actualizados con historia de la decisión; adendas a02/03/09/16/21. Sin HU nueva ni asignación retrospectiva a sprints.

| Ejecución | Resultado y alcance |
|---|---|
| [Primer catálogo](../evidencias/03-I-tests-20261110T165543164740Z/result.json) | 91 métodos,1 error: fixture de disponibilidad creaba dos productos con igual nombre. Se adaptó solo el nombre del segundo producto ficticio; se conservaron todas las aserciones de stock/estado. No fue un defecto nuevo de producción |
| [Catálogo final](../evidencias/03-I-tests-20261110T165640773189Z/result.json) | **91/91**, incluidos8 métodos nuevos de política. Check sin incidencias y makemigrations --check --dry-run sin cambios |
| [Navegador final](../evidencias/03-I-browser-20261110T165730633729Z/browser.json) | **36/36**, cero errores, Chrome157/Playwright con HTTP y ORM. 27 comprobaciones H01–12 repetidas y9 nuevas I01–09 |
| [PostgreSQL](../evidencias/03-I-postgresql-20261110T165843365196Z.json) | **8/8**, clúster exclusivo PostgreSQL18.4, READ COMMITTED, dos conexiones sincronizadas para carreras |
| [Cierre verificable](../evidencias/03-I-cierre.json) | Archivos fuente, conservación, cobertura, enlaces, base retenida y cursor |

Métodos nuevos: extremos/default en ambos servicios; máximo y CHECK; nombre inactivo/mayúsculas/espacios/NFC/presentación; edición duplicada con rollback y autoexclusión; dos formularios previamente válidos; UNIQUE y guardado parcial; IntegrityError ajeno; preflight de colisión sin escritura. Dos presentaciones distintas se guardaron; no se debilitó una prueba de homónimos para mantener verde la suite.

Navegador nuevo: I01 guardó «Leche Gloria 400 g» a partir de espacios redundantes; I02 mostró error/foco y conservó base al duplicar; I03 guardó170g como ficha diferente; I04 rechazó renombre duplicado y conservó código/precio/mínimo; I05 aceptó el nombre propio en mayúsculas; I06 reservó el nombre tras deshabilitar; I07 almacenero observó ambos nombres; I08 vendedor no pudo agregar sin stock; I09 conservó estado final. Se inspeccionaron visualmente [duplicado en alta](../evidencias/03-I-browser-20261110T165730633729Z/i02-duplicate.png) y [edición rechazada](../evidencias/03-I-browser-20261110T165730633729Z/i04-edit-duplicate.png). No hubo prueba nueva de lector de pantalla/dispositivo móvil.

PG-I01: migración desde0004 con nombres equivalentes aborta sin cambios ni registro0005. PG-I02: mínimo1000000 aborta igual. PG-I03: tras resolver explícitamente los datos ficticios, migración exitosa conserva todos los campos salvo claves recalculadas. PG-I04: alta simultánea de nombre equivalente en categorías distintas, una fila y un error name. PG-I05: dos productos intentan mismo nombre; un ganador, perdedor con todos sus campos previos. PG-I06: nombre de inactivo reservado. PG-I07: servicio de alta, edición y actualización directa rechazan1000000 sin cambios. PG-I08: venta histórica ligada conserva su snapshot completo al renombrar producto. Esta venta es preparación ficticia, no un cobro ejercitado por UI en03-I.

## Conservación, límites y reproducción

Lectura previa de la base original mediante SQLite `mode=ro`:5 productos,0 grupos de colisión normalizada,0 mínimos fuera de rango y0 claves vacías. Se guardaron solo conteos en el inventario; **no se migró la base original**. Este examen no sustituye revisar otra instalación al desplegar.

Navegador final en `datos/etapa03i-20261110T165730633729Z/audit.sqlite3`: tres categorías, seis productos UND/vencimiento obligatorio, cinco activos y uno inactivo. Mínimos0,10,10,10,999999,999999. Sin lotes/cargas/ventas/borradores; turno ficticio OPEN S/50 conservado. La edición descartada preservó los campos comerciales del snapshot. No se cerró caja ni se borraron sesiones. Contraseñas/claves de las cuentas aisladas no figuran en informes.

Cada run creó un entorno nuevo con marcador, sin cargar `.env` del usuario. Servidor127.0.0.1 efímero con desafío HMAC previo al ingreso, cookies propias. Base original, auditorías previas y XLSX conservados por hash en cada ejecución. HTTP y PostgreSQL propios detenidos con puerto cerrado; bases/evidencia retenidas. La comparación comercial usa campos enumerados por el soporte; no todas las tablas/timestamps.

Desde la raíz, ejecutar secuencialmente:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03i_run.py' tests catalog
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03i_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03i_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/cierre_etapa03i.py'
```

El cierre verifica los runs de este informe; nuevas ejecuciones conservan archivos diferentes. Suite global NO EJECUTADA;91 corresponde solo a catálogo y sus dependencias ensayadas. No se atribuyen cierres a inventario/caja/ventas. Carreras con cobro/stock, dos intenciones opuestas de estado y volumen siguen pendientes. SQL/QuerySet que cambien `name` sin recalcular `search_name` no ejecutan normalización de servicios; la restricción garantiza unicidad de la clave almacenada, no valida cualquier SQL arbitrario. No hay una política nueva para confusables/acentos eliminados ni longitudes del código.

Las migraciones0003/0004/0005 deben aplicarse al desplegar después de revisar los datos de esa instalación; no es una aplicación ya realizada sobre datos del usuario. Barcode to PC Server sigue elegido; lectura física, aviso inmediato y selección de entrega de HU-PROD-03 siguen según [plan del lector](ETAPA-03-Barcode-to-PC.md).

## Cobertura y cursor

Balance de27 CA base: **21 CUMPLE en la muestra y6 PREVISTO/FUTURO**. PROD02-CA04 deja PARCIAL por decisión aceptada y evidencia entre capas. La regla de nombre se incorpora a los criterios existentes y conserva evidencia de su falla anterior. Este balance no acredita coincidencia total: persisten extras/propuestas, despliegue real y pruebas transversales.

**Cursor exacto03-J / PROP-E00-HU-02 y PROP-E03-T01 / cambio de estado de categoría, `/productos/categorias/<uuid>/estado/`: conciliar la propuesta de confirmación e información de impacto y su alcance documental con el comportamiento ya verificado03-A/E.** No volver a preguntar máximo, homónimos, categorías generales ni código editable. No implementar esa propuesta como si ya estuviera aceptada. Lector físico conserva su cola independiente; otras etapas no cambian de estado.
