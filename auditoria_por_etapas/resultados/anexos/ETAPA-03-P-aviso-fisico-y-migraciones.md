# 03-P · Aviso físico de duplicados y ensayo de migraciones

10/11/2026, America/Lima, 21:08–21:10. Se leyó completo PROTOCOLO_COMUN y se retomó el cursor de ESTADO_GENERAL/03-N-O. El usuario confirmó disponibilidad del teléfono y realizó las cinco fases. **Sublote completado en su muestra; etapa 03 abierta.** No se despliega ni se aprueban otros módulos.

## Alcance e inventario previo

Se conserva el [inventario de 9 HU/27 CA y cuatro criterios suplementarios](ETAPA-03-inventario.md). Las clasificaciones históricas de sus secciones no sustituyen la matriz vigente. CAT03/04 siguen PREVISTO/FUTURO: editar/eliminar categorías no equivale a desactivarlas ni al admin técnico. El alcance aceptado en F/I admite categorías activas diferentes de enlatados, con UND y vencimiento obligatorio. No se selecciona venta por peso ni sin vencimiento.

Fuentes contrastadas: 08_Historias, HU-PROD-03 CA01–02 y PROD02/04; 21, adenda03-O; 09, selección03-O; 01, corte R1 de nueve HU; 02, modelos y unicidad; 03, matriz histórica PROD02; 07, RN06/28/29; 14, Sprint1; 16, S1-DB-02 y tareas PROD02; CONTROL_SPRINTS, estados históricos. La evidencia antigua no cuenta como ejecución nueva. No hay AGENTS.md hallado en el workspace/antecesores comprobados. Se detectó árbol Git ampliamente modificado antes de trabajar; se conservó. XLSX ausente desde el inicio de estas ejecuciones, sin abrirlo ni reconstruirlo; su procedencia histórica está en el inventario.

| ID/fuente | Actor, pantalla/ruta, acción, campos y salida | Clasificación previa → evidencia/estado |
|---|---|---|
| PROD03/CA01–02; PROP-03G-SCAN-T02 | ADMIN, menú Registrar producto, `/productos/nuevo/`; Escanear código → Código leído → Usar código/Cancelar; aviso inmediato | Seleccionado/implementado; físico nuevo NO EJECUTADO → P1–P3 CUMPLE muestra |
| PROD04/CA03, PROD03; RN28/29 | ADMIN, Productos → Editar `/productos/<uuid>/editar/`; mismo diálogo, UUID propio incluido en consulta | Seleccionado/implementado → P4–P5 CUMPLE muestra para aviso; no se guardó edición en P |
| PROD02/CA03/05 | Registrar producto expreso después de copiar B; ficha registrada | CUMPLE muestra: una ficha, un POST y cero altas automáticas |
| Dependencia técnica CA02 | GET `/productos/codigos/comprobar/`, barcode y product_id opcional; sin escritura; ADMIN; restantes roles 403 | CUMPLE: 8 métodos API reejecutados y dos 403 nuevos en sesiones de navegador |
| PROD01; RN29 | ALMACENERO, Catálogo de productos; fila B sin Editar. VENDEDOR, Preparar venta; acceso directo a catálogo 403 | CUMPLE en estas acciones; búsqueda de venta por B NO EJECUTADA en P |
| S1-DB-02; PROP-E03-T02; AUD03I-MIG01 | Migraciones catalog0003–0006; normalización, búsqueda/nombre único, máximo mínimo y versión de categoría | Ensayo de copia CUMPLE; despliegue real NO EJECUTADO |

Contrato de campos conservado: código obligatorio al guardar, texto 1–64 tras recorte, ASCII/letras/números/espacios/guiones; unicidad ignora espacios/mayúsculas e incluye inactivos. Campo temporal inicia vacío; copiar requiere validación local y consulta completada o aviso de fallo; no persiste por leer. product_id UUID excluye solo la ficha propia. P usa A=`00CAT03K-A`, B=`00CAT03K-B`, diez caracteres y ceros iniciales. Nombre ficticio `AUD03 P lectura física`, categoría Higiene activa, precio8.50 final con IGV, UND, mínimo10 por defecto; stock cero. No se reejecutan todas las fronteras de estos campos: permanecen en C/I/O.

Inventario inverso: mensajes «Comprobando código…», «El código de barras ya está registrado», «Sin duplicados en esta consulta. Se volverá a comprobar al guardar.» y fallo de consulta permanecen trazados en O. P comprueba los dos resultados definitivos, botón deshabilitado/habilitado, copia expresa, persistencia y roles. El panel con etiqueta y botón Confirmar es instrumentación temporal de auditoría, **no una pantalla nueva del producto**. No cambia la lógica de consulta, bloqueo o guardado.

## Ejecución física y efectos

Windows, Chrome157.0.8103.39 visible, Playwright para navegación/observación y teléfono del operador para los códigos. No se usó fill/type/pegado ni teclado sintetizado sobre ninguno de los dos campos de código. Antes del recorrido, Barcode to PC Server mostró un dispositivo conectado y la sesión anterior con33 lecturas. La inspección posterior del contador no se completó porque la ventana se minimizó; no se atribuye a ese contador la cifra nueva. La recepción nueva está acreditada por eventos del formulario y confirmación humana en cada fase. No se cambió el perfil externo.

Base nueva marcada `datos/etapa03k-20261111T020804804408Z/audit.sqlite3`; cuentas ficticias, sin cargar .env, cookies propias, desafío HMAC antes de autenticarse y servidor solo127.0.0.1. A se preparó inactivo en una ficha con venta previa; B no existía. La preparación de venta/lotes es fixture, no auditoría de recepción/cobro.

| Fase | Operación | Lecturas completas / Ctrl+A | Esperado y observado |
|---|---|---|---|
| P1 | Alta, A existente e inactivo, repetición | 9 / 9 | Aviso exacto de registrado, Usar código bloqueado, formulario/base intactos |
| P2 | Alta, reemplazar A por B nuevo | 8 / 8 | Aviso sin duplicados, copiar habilitado. Tras confirmación humana el soporte pulsó Usar código y Registrar: una sola ficha B |
| P3 | Nueva alta, releer B ya guardado | 7 / 7 | Aviso exacto, copia bloqueada; ningún segundo producto ni POST |
| P4 | Edición de A, leer A propio | 4 / 4 | Excluye solo la ficha propia, mensaje sin duplicados, copia habilitada; no se guardó edición |
| P5 | Misma edición, leer B ajeno | 6 / 6 | Aviso exacto, copia bloqueada; cancelación sin modificar A ni B |

**52/52 comprobaciones**, 34 lecturas completas, longitud máxima10, cero Enter/Tab, cero entradas en otros campos, cero envíos automáticos. El único POST fue el alta expresa. Las instantáneas comparan los campos inventariados de categorías, fichas, lotes/cantidades, carga, turno, venta, línea/snapshots y borradores; el único agregado comercial es B. No afirmar comparación exhaustiva de todas las columnas en esta muestra física: ver `snapshot()` del soporte.

ALMACENERO vio B sin enlace Editar; VENDEDOR entró a Preparar venta y obtuvo403 al pedir catálogo directamente. Ambos recibieron403 en consulta anticipada de código. Estos últimos pasos fueron automatizados, no lecturas físicas. Ninguno modificó la instantánea comercial.

[Lecturas y52checks](../evidencias/03-K-phone-check-20261111T020804804408Z/phone.json) · [Antes](../evidencias/03-K-phone-check-20261111T020804804408Z/orm-initial.json) · [Después](../evidencias/03-K-phone-check-20261111T020804804408Z/orm-final.json) · [Cierre y conservación](../evidencias/03-K-phone-check-20261111T020804804408Z/result.json). Capturas P1 y P4 inspeccionadas: mensaje legible, botón bloqueado distinguible y propio permitido. P2/P3/P5 conservadas, sin revisión visual individual adicional.

## Migraciones en copia, sin despliegue

Se creó `datos/etapa03k-migrations-20261111T020942208035Z/audit.sqlite3` copiando `r1-pmv/r1_pmv.sqlite3`. Se comprobó ausencia de archivos WAL/SHM/journal y hashes estables antes/después de copiar; la aplicación se configuró exclusivamente contra la copia. No se abrió servidor para esa copia, no se ejecutaron seeds y no se mostraron nombres, códigos, correos ni filas originales en evidencia. La copia conserva información original y debe permanecer local.

Preflight:2 categorías,5 productos; cero grupos duplicados por normalización de categoría/nombre, cero claves inválidas o vacías y cero mínimos fuera de0..999999. Plan:0003_normalize_category_spaces →0004_product_search_name →0005_product_name_and_minimum_policy →0006_category_state_version. Las cuatro se aplicaron. Django check correcto y sin cambios de migración por generar para catalog.

Integridad SQLite antes/después `ok`, cero violaciones de FK. Comparación de todas las tablas previas salvo django_migrations: mismas filas y hashes de las columnas previas, exceptuando las claves derivadas `Category.name_normalized`, `Product.search_name` y la nueva versión de categoría. Conserva nombres visibles, UUID, relaciones, precios, mínimos, inventario, ventas e identidad. Es una prueba del esquema/datos de esta copia SQLite, no de bloqueo PostgreSQL ni de despliegue completo. Base original SHA256 conservado: `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`.

[Plan, preflight, hashes e integridad](../evidencias/03-P-migrations-20261111T020942208035Z/result.json) · [Comprobaciones Django](../evidencias/03-P-migrations-20261111T020942208035Z/checks.txt).

Regresión acotada: **18/18 métodos** (8API,2 migración categoría,8 política producto), SQLite en memoria; check y makemigrations sin incidencias. [Resultado](../evidencias/03-K-tests-20261111T021009799064Z/result.json) · [Log](../evidencias/03-K-tests-20261111T021009799064Z/tests.txt). La suite global326 y PostgreSQL deO no se repitieron; sus resultados conservan su fecha y alcance.

## Cambios, hallazgos y reproducción

No se encontró un defecto funcional inequívoco nuevo en estos casos, por lo que no se cambió la aplicación. Se añadió modo `phone-check` al runner, soporte `audit03p_phone.cjs` y `audit03p_migrations.py`. El soporte no se incorpora al flujo comercial. Se corrige el traspaso documental que aún señalaba K2 como texto para un chat nuevo; los cortes anteriores se conservan como historia.

AUD03P-TEST01 (tarea técnica, implementada/verificada): prueba física del criterio existente CA02; no crea HU duplicada. AUD03P-MIG01 (tarea técnica, implementada/verificada en copia): preflight, plan y conservación. PROP-03G-SCAN-T02 queda verificada físicamente en la muestra P. No cambian horas ni estados históricos de Sprint.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' phone-check
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03p_migrations.py'
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog.test_audit03_barcode_check catalog.test_audit03_categories.CategoryMigrationAudit03Tests catalog.test_audit03_policy
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

Ejecutar secuencialmente desde la raíz. Para el modo físico: teléfono conectado, perfil Ctrl+A/BARCODE sin Enter, ventana de Chrome activa, leer etiqueta mostrada, retirar cámara y confirmar cada fase. Plazo total12min; no simular lecturas si el teléfono falta. El ensayo de copia rechaza fuente con sidecars o cambio durante la copia; no ofrece reset. Las bases y evidencias se conservan.

## Pendientes, decisiones y cursor exacto

23/27 CA base CUMPLE en sus muestras y4 futuros, más cuatro suplementarios con su evidencia anterior. P completa la prueba física nueva de PROD03; no amplía la aprobación a toda etapa03. El servidor físico terminó y su puerto quedó cerrado; las bases protegidas conservaron SHA256 en las tres ejecuciones. La base física retiene sesiones/turno/borrador ficticios y tres fichas; no se ha afirmado cierre de caja. La copia migrada queda separada de la fuente.

Despliegue real **NO EJECUTADO**. Se desconoce si el destino será SQLite local o PostgreSQL desplegado: alternativaA, respaldo y ventana local con código/estáticos/migraciones/smoke por roles; alternativaB, ensayo restaurado en PostgreSQL objetivo antes de promover. Elegir requiere identificar el destino, versión y procedimiento de reversión; el éxito en copia no autoriza inferir ese destino. Una reversión de datos no consiste solo en migrar hacia atrás:0003 y0005 no reconstruyen claves previas. Conservar respaldo verificable. No se requiere esta decisión para continuar pruebas aisladas.

**Siguiente cursor 03-Q / HU-PROD-04 CA05 / AUD03Q-CONC01:** en un clúster PostgreSQL nuevo, dos categorías activas A/B, productos P/Q con lotes vigentes, turno vendedor propio y borrador con P+Q. Primero inventariar y contrastar bloqueo de `update_product` y `checkout_sale`; después sincronizar reclasificaciones cruzadas P:A→B y Q:B→A, y cobro del borrador multiproducto, con timeout y conexiones independientes. Registrar bloqueo/deadlock/rechazo/reintento, UUID/snapshots, lotes y caja; luego reproducir el resultado mediante pantallas de ADMIN/VENDEDOR y consulta ALMACENERO. **NO EJECUTADO en P.** Es frontera de catálogo, no auditoría integral de cobro.

Recepción/retiro conserva PROP-03-RET-T01..T11 y sus decisiones en [anexo](ETAPA-03-recepcion-y-retiros-pendientes.md), etapas05/06/07/08/11/12/14/15/16. No interpretar34 lecturas como34 unidades ni desactivar una ficha como retiro selectivo por lote. Accesibilidad con lector de pantalla, recuperación de fallos, volumen y otros dispositivos siguen sin ejecución nueva.
