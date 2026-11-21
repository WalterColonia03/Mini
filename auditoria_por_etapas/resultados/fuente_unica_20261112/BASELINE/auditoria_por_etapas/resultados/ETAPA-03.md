# Adenda vigente de ETAPA-03 · 12/11/2026

**Estado actual:** 03-AJ y anexos posteriores contrastados; sin cierre integral. **Pendientes compartidos:** Catálogo/lector aceptados; valoración/recepción/legacy/migraciones pendientes. **Próximo cursor:** DOC-03AH-01 / DOC-03AI-01.

[Mapa consolidado y decisiones](conciliacion_20261112/CONSOLIDACION.md) · [Contratos de implementación](conciliacion_20261112/ENCARGOS.md) · [Verificación integrada](conciliacion_20261112/VERIFICACION.md) · [Informe original íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ETAPA-03.md).

Las decisiones nuevas se aceptan desde12/11 por delegación explícita del usuario. No se cambia el resultado histórico de una muestra ni se declara cerrado el módulo. Requisitos recién revisados requieren nueva implementación/verificación. Las referencias de línea del texto histórico remiten a BASELINE. Los anexos conservan su fecha y vigencia original; los estados actuales se consultan en el mapa.

## Rectificaciones transversales aplicables

Etapa09 sí tiene ejecución/evidencia (Chrome67funcionales+1control), aunque10–12 y estado general antiguos la dejaban pendiente. 04-D acredita revocación en sus muestras; su límite raw sin petición/servicio permanece. El fallo `_state.adding` de inventario fue corregido05-L e incluido en434tests actuales. Los informes antiguos que lo separaban no prueban fallo actual. El empate de orden de turnos no se considera corregido por repetir una corrida. Soporte12PG es DjangoClient concurrente contraPG, no redHTTP por sockets. 05-Linterrupción antes de escribir no prueba caída postwrite. HU-VEN-05b pide filtrosCA02 y detalleCA03; no hay conflicto de líneas expandidas.

---

## Informe y resultados históricos conservados

# Etapa 03 · Categorías y productos

**Continuación 03-AJ / 06-E.** 46 comprobaciones Chrome/HTTP/ORM, 6 escenarios bidireccionales de bloqueo por fila en PostgreSQL 18.4 (`identity_account`), 15 regresiones acotadas y **362/362** pruebas completas de las 6 aplicaciones (`AUDIT03K_DEFAULT_COOKIES='1'`). Corregidos: bloqueo de actor `_lock_warehouse_actor` en [`inventory/services.py`](../../r1-pmv/inventory/services.py#L71-L80), cierre explícito de sesiones inactivas en `roles_required`/`login_view`/`dashboard`, `@never_cache` en vistas de carga/entrada y relleno/ajuste de tablas en [`initial_load_created.html`](../../r1-pmv/inventory/templates/inventory/initial_load_created.html#L15). Base original y bases protegidas conservan SHA-256. [Evidencia, fallos intermedios conservados y límites](anexos/ETAPA-03-AJ-sesion-recepcion.md). **06-F / AUD06F-CONCILIACION-INV01b.** Conciliar `HU-INV-01b/CA-01..02` y `RN-01/14/28/29` frente a `03-AG..AJ` y dejar documentadas `DOC-03AB-01`, `DOC-03AH-01` y `DOC-03AI-01` antes de Etapa 04 (`HU-PROV-01/CA-01`) o Etapa 07 (`HU-PROD-06/CA-01`); despliegue, caída real de servidor, recepción multiproducto, cuarentena y retiro sanitario siguen pendientes.

## 1. Alcance, fuentes e inventario

Alcance inventariado: `catalog/`, sus formularios, modelos, servicios, plantillas, URLs, menús de entrada y efectos sobre otros roles. **9 HU / 27 CA base**, tres agregados QA pertinentes (08:872,874,876, descompuestos por acción), doce patrones de ruta (uno de vencimientos asignado a07), nueve plantillas (una de07), tres formularios comerciales y tres modelos de catálogo, incluida la reserva de claves de lectura. La administración técnica Django se identifica aparte del rol comercial ADMIN.

Se siguió completo `../PROTOCOLO_COMUN.md`; se consultaron el estado general y traspaso02, guía21, fragmentos pertinentes de01/02/03/07/08/09/14/16, CONTROL_SPRINTS y evidencia histórica de CAT/PROD. Jira no se usó. El libro XLSX solo se inventarió por la procedencia documentada y hash; no se abrió ni modificó. [Inventario y matriz individual](anexos/ETAPA-03-inventario.md) · [Captura previa a cambios](evidencias/03-inventario-20261110T000729019055Z/inventory.json).

Roles del pedido: **ADMIN gestiona; ALMACENERO consulta; VENDEDOR solo consultas de venta autorizadas**. Las pruebas de categoría incluyen visitante, ADMIN, ALMACENERO y VENDEDOR por navegador y solicitudes directas. El conflicto documental del actor de PROD01 se mantiene trazado, sin ampliar permisos.

Exclusiones de ejecución profunda03-A: PROD01/02/04/05 (salvo regresión y frontera indicada), edición/eliminación comercial de categoría y lector (futuros), vencimientos completos07, carga/reposición05/06, ciclo integral de caja/venta09–12, seguridad del admin15 y revisión normativa16. No se interpreta una prueba de frontera como auditoría de esos módulos.

Balance vigente de los27CA base. **23 CUMPLE en sus muestras y 4 PREVISTO/FUTURO** (CAT03/04). PROD03 se seleccionó en03-O; CA01 tiene evidencia físicaK9 y CA02 evidencia softwareO y físicaP: 52 comprobaciones y 34 lecturas en cinco fases. Los27 están clasificados; los cuatro futuros no fueron aprobados por ejecución. Las secciones2 a6 conservan el corte histórico03-A, incluidos sus pendientes de entonces; los resultados posteriores están en las secciones 7 en adelante y la conciliación vigente en el anexo03-W. DOC03-01 y DOC-00-14 se resolvieron en03-F; DOC03-02 en03-G, por instrucciones explícitas del usuario. No hay coincidencia total con la planificación ni aprobación de otros módulos.
**Discrepancia histórica 03-W (redacción aclarada en 03-Z):** CA01 de PROD03 conserva una discrepancia de redacción entre 08:231 (llenado automático de campo) y adenda08:912 (revisión y copia expresa). CUMPLE se refiere a la muestra del alcance posterior; no se demostró copia automática al campo final del diseño vigente. Ver [matriz y opciones](anexos/ETAPA-03-W-conciliacion.md).

> **Lectura de continuidad:** las secciones 2–6 y cada continuación fechada describen su propio corte histórico; sus frases «vigente», pendientes y cursores se interpretan a esa fecha. El encabezado y 03-AJ contienen el estado actual; 03-W conserva la conciliación anterior de catálogo.

## 2. Entorno y conservación

Windows; Python del virtualenv del proyecto; Django del proyecto; Chrome **157.0.8103.39**, automatizado con Playwright, DOM y capturas PNG inspeccionadas; viewport1366×900 y observación adicional390×844. No se usó cliente Django como sustituto del navegador: el cliente se identifica como prueba de servidor.

Base final del recorrido: `datos/etapa03a-20261110T001427294717Z/audit.sqlite3`, nueva por ejecución, marca de propiedad y clave aleatoria; cuentas ficticias `*@audit03.invalid`. El soporte deshabilita explícitamente la carga de `.env`, usa cookies propias, verifica desafío HMAC antes de enviar credenciales y escucha solo127.0.0.1 en puerto efímero. Las contraseñas de prueba quedan fuera de los informes; capturas después del ingreso y texto sin tokens. Los logs de fallos iniciales tienen los valores CSRF redactados.

Fechas de archivos usan UTC: `20261110T00…Z` corresponde al **09/11/2026 por la tarde en Lima**. No confundirlo con una nueva jornada local.

Se preservaron por SHA256 la base original, las bases00/01/02 y las ejecuciones anteriores, y el XLSX. No se ejecutó flush/reset/seed destructivo ni se migró la base original. La migración nueva se aplicó en bases aisladas. Los servidores HTTP de cada recorrido y el clúster PostgreSQL propio quedaron detenidos, con puerto cerrado comprobado. La base final retiene la muestra para trazabilidad: tres categorías, tres productos, un lote con19 unidades, una venta previa, un borrador ACTIVE con dos unidades, un turno OPEN ficticio y sesiones de prueba; **no afirmar que se cerró caja ni que se eliminaron sesiones**. No afecta a bases del usuario.

PostgreSQL **18.4**, clúster exclusivo en temporal con marcador `AUDIT03_OWNED`, base aleatoria, aislamiento READ COMMITTED, sin cargar configuración del usuario. Tres escenarios abajo; cluster detenido y conservado. La ruta concreta está en la evidencia PG, sin contraseña.

## 3. Hallazgos, correcciones y comprobación

| ID / severidad / alcance | Antes y reproducción | Corrección / después | Estado y evidencia |
|---|---|---|---|
| FIX03-01 · P1 · CAT02/CA01–02 | Alta `AUD03   Bebidas   y jugos`; otra con espacios simples generaba segunda fila. Modelo/servicio solo hacían strip | Nombre colapsa separadores con split/join; comparación casefold y UNIQUE. Migración0003 normaliza claves previas conservando nombre visible/FK; si encuentra colisión aborta antes de escribir, sin fusionar ni borrar | INCUMPLE inicial → CUMPLE muestra. T normalización/duplicado/migración; Chrome B03/B04/B14; PG03-01 |
| FIX03-02 · P2 · CAT02/CA02–03 | Mensajes «Ya existe…» / «Este campo…» no eran los previstos. POST vacío producía formulario no ligado, sin error | Mensajes exactos «La categoría ya existe» y «El nombre es obligatorio»; ligar cualquier POST, incluso vacío | Corregido. T vacíos `{}`, vacío y whitespace; B04/B05/B09 |
| FIX03-03 · P1 · servidor categoría | Comprobación exists seguida de insert sin recuperación: UNIQUE podía elevar IntegrityError. Servicio aceptaba nombres más largos que el modelo permite en PG | Validación del modelo antes de guardar; límite también de clave casefold; savepoint y traducción solo de colisión realmente existente; otros IntegrityError se propagan | Corregido. T race simulado/límites/error ajeno; PG carrera real y expansión de ß; no se afirma cubrir todas las carreras del catálogo |
| FIX03-04 · P2 · accesibilidad de error | Django emitía `aria-describedby=id_name_error` pero plantilla no tenía ese destino | ID del mensaje asociado al campo y role=alert para mensajes | Corregido en DOM/visual. B05/B06 y T accesibilidad. Lector de pantalla real NO EJECUTADO |
| E03-EXTRA-01 · P1 decisión · categoría | Activar/Desactivar no borra ni edita nombre; estado afecta varios roles | Ya implementado antes de esta sesión y respaldado por agregado08:876. Se comprobó efecto; no se reatribuyó a CAT04 | EXTRA SIN HU dedicada; PARCIAL frente a PROP-E00-HU-02 por confirmación/reintentos/estado objetivo pendientes |
| DOC03-01 / DOC-00-04 · P1 alcance | R1/DEC04/RN03/PROD02 limitan enlatados/categoría seed; QA876 habilita cualquier activa | Chrome B14b registró **«AUD03 Jabón de prueba»** en categoría nueva, precio3,50, mínimo10, UND, vencimiento=true, stock0. La UI seguía diciendo «Registrar producto enlatado» | CONFLICTO DE FUENTES comprobado, no se impuso clasificación comercial por el nombre del artículo |
| DOC03-02 · P1 alcance | PROD04/CA03 bloquea código; QA872, formulario/servicio y pruebas permiten editarlo preservando snapshots | Conflicto inventariado; pruebas históricas de edición pasaron, sin cambio de política | Decisión pendiente para03-C; no bloquear campo ni retirar funcionalidad sin resolver fuentes |
| DOC-00-14 · P1 trazabilidad | HU-PROD01 dice administrador/vendedor; guía21 y aplicación usan administrador/almacén | Pedido de esta etapa define consulta vendedor en venta autorizada. Se mantuvo ese límite; la HU requiere conciliación explícita | Alcance operativo definido por usuario; discrepancia documental pendiente, sin ampliación de permisos |
| E03-OBS-01 · P1 candidato · PROD01 | Plantilla de catálogo contiene mínimo y disponibilidad, no existencias ni señal ligada al umbral | Observación estática, B20 solo vio estado de categoría | No aprobado. Primer caso03-B debe reproducir contra stock conocido antes de corregir |

Cambios de aplicación limitados a `catalog/models.py`, `forms.py`, `services.py`, `views.py`, `templates/catalog/category_form.html`, nueva `migrations/0003_normalize_category_spaces.py` y nuevo `test_audit03_categories.py`. Se conservaron los cambios preexistentes, incluidos producto, ventas y roles. No se reescribieron los estados históricos del backlog/sprints.

**Migración pendiente fuera del entorno aislado:** necesita respaldo/despliegue gestionado. Si los datos previos contienen dos categorías equivalentes tras colapsar espacios,0003 entrega sus UUID y falla de forma segura, sin elegir cuál conservar. Resolver la duplicidad requiere decisión de datos; no se inspeccionó ni fusionó la base real. El reverse es noop: no recupera el espaciado antiguo de las claves. El nombre visible histórico y referencias se conservan; nuevas altas guardan nombre limpio.

## 4. Efecto entre roles observado

Se preparó una venta histórica por servicio como **fixture**, un lote20 y un borrador posterior de dos unidades. La venta fixture consume1; el estado inicial de la prueba de categoría tiene19. Esta preparación no constituye una auditoría del cobro ni del FEFO.

1. ADMIN desactiva categoría desde menú/lista; fila sigue visible como Inactiva.
2. VENDEDOR busca código en mostrador: desaparece el resultado, pero el borrador conserva su línea. Intentar cantidad3 rechaza con «El producto seleccionado no está disponible para la venta.»; queda cantidad2.
3. Confirmar cobro rechaza indicando que el producto ya no está disponible y debe quitarse. No cambia venta, líneas históricas, borrador, stock ni turno.
4. ALMACENERO no ve esos productos en selectores de carga inicial/entrada; catálogo dice «Categoría desactivada». Servicios directos de carga inicial y entrada también rechazan, sin mutaciones. No basta con ocultar la opción.
5. Constancia histórica del vendedor conserva texto y snapshots. Reactivar categoría recupera búsqueda y selector de entrada; no modifica productos, lotes, borrador, venta o caja.

Evidencia navegador B15–B22 y prueba `CategoryEffectsAudit03Tests`. **Desactivar el producto** tiene una regresión automática preexistente ejecutada; su recorrido independiente con navegador, cambios de precio/código e históricos ampliados queda en PROD05/03-C. No se presume equivalencia completa con desactivar categoría.

## 5. Pruebas y evidencia reproducible

| Ejecución | Resultado exacto | Evidencia |
|---|---|---|
| Antes de corregir:18 métodos | 13 fallos de aserción/subcasos y1 error. No son14 defectos distintos ni14 métodos necesariamente fallidos; algunos subcasos acumulan filas por el mismo defecto | [Tests iniciales redactados](evidencias/03-A-tests-20261110T000927933696Z/tests.txt) |
| Chrome inicial | 15 observaciones:10 positivas,5 negativas; después se interrumpió por selector ambiguo al existir duplicados. B13 en adelante NO EJECUTADO en ese recorrido. Se corrigió el selector del soporte para usar UUID | [Resultado inicial](evidencias/03-A-browser-20261110T001124615788Z/browser.json) |
| Después de corregir:18 métodos | 18/18; check y makemigrations --check --dry-run sin incidencias | [Corte intermedio](evidencias/03-A-tests-20261110T001235417602Z/result.json) |
| Regresión final ampliada | **53/53 métodos**:15 nuevos (12 categoría,2 migración,1 efecto servicios),36 `catalog.tests` y2 fronteras inventory/sales. Check y migraciones sin cambios pendientes | [Comando/resultado](evidencias/03-A-tests-20261110T001337606973Z/result.json) · [Log](evidencias/03-A-tests-20261110T001337606973Z/tests.txt) |
| Chrome final ampliado | **28/28 observaciones** B00–B23 (B12 separado por rol, B14b/c). Incluye navegador, solicitudes HTTP y snapshots ORM; B23 solo observación visual, no prueba completa de usabilidad móvil | [Observaciones](evidencias/03-A-browser-20261110T001427294717Z/browser.json) · [Cierre](evidencias/03-A-browser-20261110T001427294717Z/result.json) · [Persistencia final](evidencias/03-A-browser-20261110T001427294717Z/orm-final.json) |
| PostgreSQL real | **3/3 escenarios**: dos altas canónicamente iguales sincronizadas antes de INSERT→una fila y un rechazo exacto; dos categorías distintas→dos filas; clave expandida >120→ValidationError | [PG03-01..03](evidencias/03-A-postgresql-20261110T001529034853Z.json) |

Las53 pruebas son una sola ejecución final; no sumar18+18+53 ni26+28 como cobertura independiente. La suite completa del proyecto **NO EJECUTADA**. La concurrencia PG de categorías no demuestra carreras de desactivación frente a inventario/cobro ni seguridad de despliegue.

Comandos desde la raíz del workspace, todos crean entornos nuevos y conservan los anteriores:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03_run.py' tests catalog.test_audit03_categories catalog.tests inventory.tests.PhysicalAdjustmentTests.test_bug033_inactive_category_excludes_products_from_initial_load_and_stock_entry_forms sales.tests.SalesHistoryTests.test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03_pg.py'
```

No ejecutar los modos internos `effects/serve` fuera de la base marcada. No reutilizar el runner de etapas anteriores con reset. El informe final incluye [verificación de conservación y cambios](evidencias/03-A-cierre.json).

Capturas revisadas: [alta categoría](evidencias/03-A-browser-20261110T001427294717Z/B03-created.png), [error asociado](evidencias/03-A-browser-20261110T001427294717Z/B05-empty-error.png), [producto no enlatado aceptado](evidencias/03-A-browser-20261110T001427294717Z/B14b-noncanned.png), [venta con categoría inactiva](evidencias/03-A-browser-20261110T001427294717Z/B16-inactive-sale.png), [rechazo de cobro](evidencias/03-A-browser-20261110T001427294717Z/B18-checkout.png), [vista móvil](evidencias/03-A-browser-20261110T001427294717Z/B23-mobile.png). En móvil la tabla tiene desplazamiento interno; no se auditó operabilidad por teclado/táctil ni todos los tamaños.

## 6. Propuestas y decisiones, sin inventar aceptación

**DOC03-01, alcance de productos — pendiente.** Alternativa A: mantener R1 restringido a enlatados y documentar por separado la ampliación ya existente; requiere decidir qué hacer con productos/categorías adicionales antes de restringir nuevos registros. B: aceptar productos por unidad y con vencimiento obligatorio, actualizar título/ayudas/PROD02/RN03/DEC04 y matriz sin borrar la línea base R1. C: venta general con productos sin vencimiento o por peso; implica nuevas HU/reglas/modelos/lotes y está fuera de este sublote. No basta cambiar el título para implementar C.

**DOC03-02, código editable — pendiente.** A: bloquear cambios futuros y conservar históricos de cambios ya hechos; B: aceptar corrección ADMIN con código normalizado único, preservación de FK y snapshots históricos, comportamiento de borradores definido y prueba de concurrencia. La opciónB describe más del comportamiento existente, pero contradice el CA base y no se acepta automáticamente.

**DOC-00-14, actores — propuesta de conciliación.** Para el alcance indicado por el usuario, redactar PROD01 con ADMIN/ALMACENERO; vincular consulta VENDEDOR a VEN01b y a turno/propiedad, sin acceso al catálogo administrativo. No borrar la redacción histórica; indicar fecha y decisión al actualizar08/09/21.

**PROP-E00-HU-02, estado de categoría — ampliación de propuesta existente, no nueva HU duplicada.** Actor ADMIN; necesidad suspender operaciones de un grupo conservando existencias e historial; precondición categoría existente y permisos vigentes. Implementado previamente y verificado03-A: exclusión en alta/listas de entrada/venta, rechazo de actualizar/cobrar, conservación histórica, reactivación condicionada a producto activo y stock. Pendiente de aceptación:

- CA propuesto03-A: Dada una categoría activa, cuando ADMIN confirma la suspensión con explicación del impacto en productos, borradores e inventario, entonces se establece inactiva sin borrar ni modificar movimientos confirmados; errores de permiso/UUID no alteran filas.
- CA propuesto03-B: Dado el reenvío del mismo estado objetivo, cuando se repite una solicitud o se usa una pestaña antigua, entonces se conserva el estado o se informa conflicto; nunca se revierte por el mero reintento. Entradas: UUID y estado booleano explícito, CSRF; salida: estado persistido y mensaje exacto. El endpoint actual **alterna**: este criterio está PROPUESTO, no implementado/verificado.
- CA propuesto03-C: Dada la reactivación, cuando se consulta venta, entonces solo vuelven los productos activos con stock vigente; productos individualmente inactivos no se reactivan. Verificado caso simple; combinación completa y carreras pendientes.
- Tarea técnica **PROP-E03-T01**: resolver idempotencia/control de versión del cambio de estado, confirmación e información previa, pruebas de dos administradores y concurrencia PostgreSQL con inventario/cobro. PROPUESTA, no HU ni tarea completada.

**PROP-E03-CA01, límites del nombre de categoría — propuesta documental.** Añadir a CAT02: nombre obligatorio con letra/número, máximo120 caracteres tras reglas acordadas, clave casefold≤120, colapsar whitespace conservando espacios significativos entre palabras; duplicado contra activas e inactivas; rechazos sin escrituras; error vinculado al campo. Topes/alfanumérico son guardas existentes o aclaraciones técnicas, no convertirlas en aceptación comercial implícita. Resolver aparte equivalencia de acentos/NFC, caracteres invisibles y límites de expansión, sin afirmar cobertura Unicode exhaustiva.

**PROP-E03-T02, datos previos — implementada y verificada en muestra aislada.** Migración de claves con preflight de colisiones, sin renombrar/fusionar/borrar; casos automático de éxito y abortar sin escritura. Despliegue/migración sobre datos de uso real PENDIENTE; no necesario para cerrar este sublote aislado.

**PROP-E03-TEST01, completar matriz productos — pendiente03-B/C.** Inventariar y ejecutar límites por campo y salida, mensajes exactos, altas/ediciones/estado denegados por rol, historiales y borradores con cambio de precio/código, categoría y producto desactivados juntos; reflejar casos en matriz vigente nueva sin alterar resultados históricos de03 ni las etiquetas de CONTROL_SPRINTS. Cada ampliación debe quedar como propuesto/aceptado/implementado/verificado según evidencia.

CAT03/04 y PROD03 se mantienen **futuros**: admin técnico no valida la experiencia comercial de editar/eliminar, y que un lector emule teclado no acredita detección de lectura ni mensaje inmediato de duplicado. No se implementaron ni eliminaron estas funciones para simular coincidencia.

## 7. Resultado del sublote 03-B

**HU-PROD-01, CA-01 a CA-03 · CUMPLE en los roles y datos ensayados.** Se reprodujo E03-OBS-01. El catálogo omitía las unidades disponibles y el aviso de stock bajo. Ahora muestra la suma de los lotes con vencimiento posterior a la fecha de Lima y compara esa cantidad con el mínimo de cada artículo. En la muestra de 62 unidades físicas aparecieron 9 vigentes y la etiqueta «Stock bajo». El estado del producto y de la categoría continúa indicando si esas unidades pueden ofrecerse en venta.

La búsqueda por nombre pasó las pruebas con «Atún», «ATÚN» y el acento compuesto con dos caracteres. El código conserva su propia regla de normalización. Una consulta con carácter nulo ahora muestra un error junto al campo. Al regresar a una búsqueda previa con el botón Atrás de Chrome, coinciden URL, campo y resultados.

En datos aislados se ejecutaron **62 métodos de Django, 43 comprobaciones de navegador/HTTP/ORM y 5 comprobaciones PostgreSQL**. La prueba de migración en PostgreSQL recorrió el paso desde el esquema 0003 con un producto previo hasta 0004. Aplicar `catalog.0004_product_search_name` al entorno de uso queda pendiente de despliegue. La auditoría conservó la base original, las bases anteriores y el libro XLSX. Los servidores de prueba quedaron detenidos. [Casos, archivos, comandos y limitaciones](anexos/ETAPA-03-B-catalogo.md) · [Cierre reproducible de 03-B](evidencias/03-B-cierre.json).

## 8. Resultado del sublote 03-C

El alta nominal de HU-PROD-02 guardó «Atún de prueba» en «Productos enlatados», con unidad UND, S/ 8,50 de precio final, mínimo 10, vencimiento obligatorio y cero existencias. ALMACENERO pudo consultar la ficha desde el catálogo. VENDEDOR buscó desde su turno y no pudo agregarla a la venta. Ambos recibieron 403 en las rutas administrativas de alta y confirmación.

Los criterios de precio, código y stock inicial/permisos cumplen en la muestra. **CA-01 sigue en CONFLICTO DE FUENTES** porque también fue posible registrar «Jabón neutro» en «Higiene» con vencimiento obligatorio. **CA-04 queda PARCIAL**. Se guardaron vacío como 10, cero y 999 999. Se rechazó 1 000 000. HAL-005 describe la guarda técnica y el criterio de negocio carece de límite superior explícito.

Se corrigieron el POST vacío, los mensajes contradictorios, los límites y ayudas del formulario, el foco al fallar y la detección sucesiva de nombres con mayúsculas acentuadas. El servicio revalida la categoría activa dentro de la transacción de alta. Se completaron 68/68 métodos de catálogo, 49/49 comprobaciones de Chrome/HTTP/ORM y 5/5 en PostgreSQL. Una observación aparte reprodujo dos productos homónimos con códigos distintos al guardar formularios previamente validados. Se proponen opciones en PROP-03C-NOMBRE. [Fuentes, casos, capturas y reproducción](anexos/ETAPA-03-C-alta.md) · [Cierre del sublote](evidencias/03-C-cierre.json).

## 9. Resultado del sublote 03-D

Se recorrieron los cinco criterios de HU-PROD-04. Precio, mínimo, nombre y categoría cumplen en la muestra. El código permanece editable y el CA-03 conserva el conflicto DOC03-02. La venta histórica mantuvo nombre, código y S/ 8,50. Al editar el precio a S/ 9,20, la consulta del vendedor mostró el valor nuevo y el borrador conservó el anterior hasta confirmar el cobro. El primer intento actualizó el precio pendiente y mostró una advertencia. El segundo cobró dos unidades por S/ 18,40. Una nueva incorporación tomó 9,20.

Se corrigieron el POST vacío, el duplicado de nombre con mayúsculas acentuadas, las ayudas y el foco de error, la reclasificación hacia una categoría recién suspendida y el desbordamiento del mensaje de éxito. Se recuperó el vínculo de un detalle heredado sin producto al cambiar el código desde el formulario, conservando sus campos históricos. El servicio toma el código anterior de la base y lee producto y categoría bajo bloqueo.

Pasaron **76/76 métodos, 51/51 comprobaciones Chrome/HTTP/ORM y 4/4 escenarios PostgreSQL**. La primera venta fue dato de preparación y la segunda se cobró en navegador. El corte conserva un borrador ACTIVE y un turno OPEN ficticios, con 17 unidades en el lote. [Matriz, propuestas, capturas y comandos](anexos/ETAPA-03-D-edicion.md) · [Conservación y cobertura](evidencias/03-D-cierre.json).

## 10. Resultado del sublote 03-E

Los tres criterios de HU-PROD-05 cumplen en la muestra. Deshabilitar excluye el producto de la búsqueda de venta y de selectores de inventario; actualizar su línea y cobrar rechazan en servidor. Se conservan los campos observados de inventario, borrador, turno y venta histórica. Reactivar recupera19 unidades vigentes y S/8,50 cuando la categoría está activa; categoría inactiva, cero existencias y solo vencidos siguen impidiendo venta. Se recorrieron las cuatro combinaciones de estado producto/categoría.

Se reprodujeron y corrigieron el reintento que reactivaba accidentalmente producto o categoría, la lectura de estado antiguo en el servicio y las etiquetas/mensajes que confundían activación con disponibilidad efectiva. Los botones ahora envían el estado solicitado; el servicio lee y bloquea la fila y guarda solo el cambio necesario. «Inactivo» coincide con CA03. La compatibilidad de peticiones antiguas sin estado sigue alternando, límite documentado.

Pasaron **82/82 métodos de Django, 34/34 comprobaciones Chrome/HTTP/ORM y 6/6 PostgreSQL**. Check y detección de migraciones sin incidencias. PostgreSQL ejercitó dos sesiones de la misma cuenta sincronizadas al solicitar bloqueo; no probó dos administradores con decisiones opuestas ni suspensión concurrente con cobro. La suite completa del proyecto no se ejecutó.

Base final retenida `datos/etapa03e-20261110T033002861512Z/audit.sqlite3`: una categoría, tres productos, dos lotes con19 vigentes y4 vencidas, una venta, un borrador ACTIVE de dos unidades, otro DISCARDED de preparación y un turno OPEN. Servidores propios detenidos; base original, bases anteriores y XLSX conservados por hash. La comparación inicial/final comprende los campos enumerados en el anexo, no todas las tablas ni timestamps. [Casos, cambios, capturas, comandos y límites](anexos/ETAPA-03-E-disponibilidad.md) · [Cierre verificable](evidencias/03-E-cierre.json).

## 11. Conciliación de pendientes al cierre03-E (histórica)

**03-F / DOC03-01 / HU-PROD-02 CA01, 08:218 frente a08:876 y16:328.** Próxima acción: registrar una decisión entre A) mantener enlatados y resolver los datos adicionales existentes, B) aceptar cualquier producto por unidad con vencimiento obligatorio, o C) planificar venta general con otras unidades/sin vencimiento. Las consecuencias están en§6. Hasta decidir, el conflicto se conserva y no se restringen datos ni se cambia silenciosamente la planificación. Seguir con DOC03-02/PROD04-CA03 (08:243 frente a08:872), máximo del mínimo y homónimos. La etapa04 permanece NO EJECUTADA; no forma parte de este cierre.

| Pendiente o propuesta | Estado vigente y siguiente acción |
|---|---|
| DOC03-01 / DOC-00-04 | CONFLICTO comprobado: la interfaz acepta otros productos. Elegir alcance y actualizar08/09/21/RN03/DEC04 con fecha y trazabilidad |
| DOC03-02 | CONFLICTO comprobado: código editable frente a criterio que lo bloquea. Conservar conducta y evidencia hasta decidir |
| PROP-03C-LIMITES | PARCIAL PROD02-CA04: tope999999 no recogido en criterio. Acordar máximo y reflejarlo en08/03 |
| PROP-03C-NOMBRE | Duplicado de nombre puede persistir entre formularios previamente validados. Elegir homónimos permitidos/advertidos o unicidad normalizada con tratamiento de datos previos |
| DOC-00-14 | Usuario fijó roles operativos. Propuesta: PROD01 ADMIN/ALMACENERO, VENDEDOR en consulta de venta autorizada; actualizar fuente sin borrar línea histórica |
| PROP-E00-HU-02 / PROP-E03-T01 | Estado de categoría extra sin HU dedicada aceptada. Reintento explícito implementado/verificado03-E; confirmación e información de impacto, control de versión y dos intenciones opuestas siguen pendientes |
| PROP-E03-TEST01 | Muestra de límites, mensajes, roles, históricos y combinaciones de los sublotes03-B aE ejecutada. No equivale a pruebas exhaustivas: volumen, Unicode adicional, dispositivo/lector de pantalla y otros navegadores pendientes |
| PROP-03E-CA01 | Aclaración propuesta de precondiciones de reactivación: categoría activa y stock vigente. Conducta verificada, aceptación documental pendiente |
| PROP-03E-TEST01; datos heredados con código reutilizado | Carreras con inventario/cobro, dos administradores y todos los históricos →12/15. Sin ejecutar aquí |
| PROP-E03-T02 y migraciones0003/0004 | Verificadas en aislado; despliegue sobre datos de uso real pendiente. Si hay categorías equivalentes,0003 aborta; resolver colisión sin fusión automática |
| CAT03/04, PROD03 | Seis CA futuros: editar/eliminar categoría y escáner. Administración técnica no acredita flujo comercial. No implementados por esta auditoría |
| Reglas transversales | Cantidad/umbral consolidado→07; carga/reposición→05/06; caja/venta/historial íntegros→09–12; integración→14; seguridad/admin/concurrencia→15; normativa→16 |

Las propuestas se registran como tales, con criterios/tareas/pruebas en los anexos. No se modificaron estados históricos de backlog, sprints ni XLSX para aparentar aceptación. Se puede revisar cada dirección de trazabilidad en la matriz:27 CA→evidencia y cada superficie/campo/acción→HU, agregado QA, extra o futuro.


## 12. Decisión aplicada y verificación03-F (corte histórico)

El usuario aceptó **productos de cualquier categoría, por unidad y con vencimiento obligatorio**. Se actualizó HU-PROD-02/CA01, RN03 y la descripción del cálculo uniforme existente en RN30, con adendas a alcance, diseño, backlog, tareas y matriz. Se conserva R1 como línea base histórica. El formulario ahora dice «Registrar producto» y explica categoría activa, UND y vencimiento obligatorio. El modelo y los servicios ya soportaban ese alcance. DOC-00-14 se concilió con el pedido original: ADMIN gestiona y ALMACENERO consulta catálogo; VENDEDOR consulta en su venta autorizada.

Pasaron **20/20 métodos y53/53 comprobaciones Chrome/HTTP/ORM** en base nueva. Se verificaron alta en Higiene, rechazo de KG/categorías inválidas, persistencia de vencimiento obligatorio pese a POST manipulado y consultas entre roles. Tres productos sin lotes/ventas/borradores, turno OPEN ficticio conservado. Base original, bases anteriores y XLSX sin cambios; servidor detenido. No se repitió PostgreSQL al no cambiar servicios ni esquema. [Anexo completo](anexos/ETAPA-03-F-alcance.md) · [Cierre03-F](evidencias/03-F-cierre.json).

**Cursor03-G / DOC03-02 / HU-PROD-04 CA03 (08:243 frente a08:872).** La política de código editable sigue por aclarar. El usuario indicó Barcode to PC Server como solución de lectura; esto se registra sin declarar implementados ni aprobados los dos criterios de escáner. Pendientes restantes: máximo del mínimo, homónimos, confirmación/versión de estados y pruebas transversales. Las alternativas de§6/11 conservan vigencia salvo DOC03-01 y DOC-00-14, ya resueltos. Otras etapas mantienen su estado.


## 13. Código editable aceptado y resultado03-G

El usuario aceptó **corrección administrativa del código si es único y conserva históricos**. HU-PROD-04/CA03 y las adendas de diseño, backlog, tareas, matriz y guía actual reflejan la decisión; la redacción anterior queda registrada. El comportamiento ya estaba implementado. Pasaron **10/10 métodos y53/53 comprobaciones Chrome/HTTP/ORM** en la repetición final. Dos fallos iniciales correspondieron a la selección de una línea descartada y una expectativa mal copiada en el soporte; se corrigieron y se retuvo el resultado inicial.

La prueba guardó código nuevo, actualizó búsquedas y conservó la constancia anterior; rechazó duplicados e inválidos y verificó permisos. El recorrido ampliado dejó lote17, dos ventas, un borrador ACTIVE1 y turno OPEN ficticio. Se conservaron original, bases anteriores y XLSX; servidor detenido. No hubo cambios funcionales de aplicación ni nueva ejecución PostgreSQL en03-G. [Resultado y límites](anexos/ETAPA-03-G-codigo-y-lector.md) · [Cierre verificable](evidencias/03-G-cierre.json).

**Barcode to PC Server** quedó identificado por el usuario. La documentación oficial describe emulación de teclado; se propone perfil de captura sin guardado automático y foco explícito en Código. La simulación conservó ceros iniciales, pero también reprodujo ausencia de aviso inmediato al terminar un duplicado. HU-PROD-03 conserva dos criterios futuros/pendientes de incorporación; el lector real no fue probado. [Fuentes oficiales, tareas y pruebas concretas](anexos/ETAPA-03-Barcode-to-PC.md).

**Cursor03-H / PROP-03C-LIMITES / HU-PROD-02 CA04,08:221.** Acordar máximo del stock mínimo: se mantiene999999 hasta decisión. Después política de homónimos (PROP-03C-NOMBRE), selección del trabajo de lector y prueba móvil→servidor→navegador. DOC03-01/DOC03-02/DOC-00-14 ya están resueltos; las secciones históricas que los marcaban pendientes no constituyen el estado actual. Persisten confirmación/control de versión de estados, despliegue de migraciones y pruebas transversales. Ninguna otra etapa cambia de estado.

## 14. Validación del mínimo y resultado03-H

Se profundizó el contrato del stock mínimo entre formulario, servicios y persistencia. RN06 ya exige entero: se reprodujo que llamadas internas al alta/edición truncaban0.5 a0 y Decimal1.5 a1, y aceptaban True como1. **FIX03H-01** ahora rechaza esos valores y los no finitos antes de la conversión del campo. La edición inválida conserva todos los campos de Product. No cambió el esquema ni se impuso un máximo comercial.

Pasaron **24/24 métodos y27/27 comprobaciones Chrome/HTTP/ORM**. Los dos métodos nuevos fallaron antes de corregir; la primera ejecución de navegador abortó por una cabecera de aislamiento mal copiada en el soporte, antes del ingreso. Se corrigió y repitió conservando evidencia. Las pruebas finales observaron alta vacía/omitida10, cero y999999, edición, errores, lectura de almacenero, consulta de vendedor y rechazo de mutaciones por roles no autorizados. Check y migraciones sin cambios. PostgreSQL y suite global NO EJECUTADOS en este corte.

**PROD02-CA04 sigue PARCIAL**: el formulario rechaza1000000 y el servicio lo admite. La decisión de máximo todavía no consta; tampoco la de homónimos. No se infiere una respuesta de «continúa». Ambas alternativas y sus tareas/pruebas están documentadas. Las decisiones anteriores sobre categorías y código siguen vigentes.

Base del navegador final: cuatro productos con mínimos0,10,10,999999, tres categorías, sin lotes/ventas/borradores y turno OPEN ficticio conservado. Base original, anteriores y XLSX sin cambios; servidores propios detenidos. [Anexo, evidencia y reproducción](anexos/ETAPA-03-H-minimo.md) · [Cierre verificable](evidencias/03-H-cierre.json). Informe actualizado el10/11; ejecución conservada del09/11,23:26–23:30 Lima.

**Cursor: 03-H / PROP-03C-LIMITES / HU-PROD-02 CA04,08:221 — recibir decisión del máximo y unificar capas; después PROP-03C-NOMBRE.** No rehacer FIX03H-01 ni las decisiones aceptadas. Balance20 CUMPLE en muestra,1 PARCIAL y6 futuros. No se cierra otra etapa.


## 15. Decisiones de mínimo y nombre aplicadas03-I

El usuario aceptó las recomendaciones con «bien, continua»: máximo999999/predeterminado10 y nombres únicos ignorando mayúsculas/espacios redundantes. Se actualizó el criterio/RN06 y se aplicó el máximo en servicio, modelo y CHECK. La clave normalizada de nombre ahora es UNIQUE; alta/edición recuperan conflictos con error del campo y sin guardar cambios parciales. La propia ficha puede conservar su nombre; una presentación distinta se distingue en el texto. Se mantienen acentos y equivalencia NFC; los históricos conservan su snapshot.

Pasaron **91/91 métodos de catálogo,36/36 comprobaciones Chrome/HTTP/ORM y8/8 PostgreSQL**. Una fixture antigua repetía el nombre para probar estados distintos; se ajustó solo el nombre ficticio conservando las aserciones y el resultado inicial90/91. Las carreras de alta/edición dejaron un ganador y un rechazo. La migración0005 abortó sin escribir ante nombres equivalentes o mínimo incompatible; tras resolver los datos ficticios se aplicó conservando campos comerciales.

Base original examinada solo en lectura:5 productos sin conflictos, no migrada. El recorrido aislado retiene6 productos (uno inactivo), sin lotes/ventas/borradores, turno OPEN ficticio conservado. HTTP/PG detenidos, original/bases anteriores/XLSX intactos. Despliegue0003/0004/0005 pendiente; suite global no ejecutada. [Detalle, capturas y reproducción](anexos/ETAPA-03-I-politicas.md) · [Cierre](evidencias/03-I-cierre.json).

**Balance vigente21 CUMPLE muestra y6 PREVISTO/FUTURO.** CA04 deja PARCIAL por decisión y prueba; no implica coincidencia total. **Cursor03-J / PROP-E00-HU-02 y PROP-E03-T01 / estado de categoría en /productos/categorias/<uuid>/estado/: conciliar confirmación e información de impacto con alcance documental y evidencia03-A/E.** No implementar la propuesta como aceptada ni reabrir decisiones resueltas. Barcode to PC Server conserva lectura física/aviso inmediato pendientes; no se cierra otra etapa.


## 16. Confirmación y conflicto de estado de categoría en 03-J

El usuario aceptó la confirmación con explicación del impacto y el rechazo de pantallas antiguas. Se incorporaron cuatro criterios suplementarios bajo PROP-E00-HU-02. Abrir y cancelar preservan los datos. En el ejemplo de tres productos, un borrador activo y 23 unidades físicas, la suspensión bloqueó la oferta, la actualización del borrador y el cobro. El almacenero conservó las cantidades y la venta confirmada mantuvo su constancia. Un segundo administrador que trabajaba con la versión anterior recibió un aviso y pudo volver a la lista.

Pasaron 98 métodos de catálogo, 32 comprobaciones de navegador/HTTP/ORM, tres escenarios concurrentes de SQLite y cuatro de PostgreSQL, incluida la migración con datos previos. Se corrigió un error interno de SQLite haciendo que el cambio de estado compruebe la versión en la propia escritura. Los datos de uso se conservaron. Las migraciones 0003 a 0006 quedan pendientes de despliegue.

**Cursor 03-K / HU-PROD-03 CA01 / PROP-03G-SCAN-T01.** En un alta ADMIN aislada, enfocar Código de barras y comprobar la captura física con Barcode to PC Server, ceros iniciales y ausencia de guardado automático. Si falta el dispositivo, registrar NO EJECUTADO y continuar con PROP-03E-CA01 / HU-PROD-05 CA02. Continúan pendientes el aviso inmediato de duplicado, la carrera de suspensión con cobro/entrada, la revisión de vías técnicas y el despliegue. El balance base sigue en 21 criterios que cumplen en la muestra y 6 futuros. Los cuatro criterios adicionales tienen evidencia propia. [Matriz, límites y pruebas](anexos/ETAPA-03-J-estado-categoria.md) · [Cierre](evidencias/03-J-cierre.json).

## Etapa 03-K

HU-PROD-03/CA01 quedó PARCIAL en el ensayo físico. El teléfono mostró las dos etiquetas EAN-13 como UPC-A de 12 dígitos. El campo de alta no recibió caracteres y ninguna de las dos bases creó productos. El segundo intento terminó con el campo vacío, cero Enter/Tab y cero POST. Barcode to PC Server 3.18.1 mostró cero dispositivos y la app 5.0.9 indicó que no podía acceder. La dirección seleccionada no coincidía con una IPv4 activa del PC y, después de los intentos, Windows no mostró ningún proceso escuchando en TCP 57891. La causa definitiva de conexión sigue abierta.

El usuario aceptó PROP-03E-CA01 como precisión de HU-PROD-05/CA02. Se verificaron 5 reactivaciones entre ADMIN, ALMACENERO y VENDEDOR, con **31/31 comprobaciones y 8/8 métodos Django**. Solo se ofreció la ficha de categoría activa con 19 unidades vigentes a S/ 8,50. Se conservaron inventario, borrador, venta y constancia. El corte documenta los fallos previos del soporte y las repeticiones. [Pruebas y reproducción de 03-K](anexos/ETAPA-03-K-lector-y-reactivacion.md).

**Cursor 03-K2 / HU-PROD-03 CA01 / PROP-03G-SCAN-T01.** Verificar escucha del servidor y vinculación del teléfono, y después probar la etiqueta Code 128 literal `00CAT03K` en un alta nueva. El aviso inmediato de duplicados, la concurrencia con cobro/entrada y el despliegue 0003–0006 permanecen pendientes. Los seis criterios futuros conservan su estado de planificación.


## Continuación 03-K2

El 10/11/2026 a las 12:58 Lima, después de que el usuario informó la conexión, la lectura física Code 128 llegó al campo ADMIN como 00CAT03K, con ocho eventos de entrada y ambos ceros iniciales. Se observó inmediatamente Enter, envío POST y navegación a la ficha registrada. La base aislada guardó exactamente un producto con ese código, precio 8.50, mínimo 10, UND y vencimiento obligatorio. HU-PROD-03/CA01 CUMPLE en esta muestra física. La propuesta de revisar antes de guardar queda pendiente de ajustar el perfil de salida. El perfil interno del lector y sus versiones después de la reconexión no se inspeccionaron. La prueba acredita el resultado de extremo a extremo en navegador y persistencia, con conexión informada por el operador. El servidor Django finalizó y todos los archivos protegidos conservaron sus hashes.

**Cursor 03-K3 / PROP-03G-SCAN-T01.** Configurar la salida del lector para enviar el código sin Enter y repetir una lectura física en alta nueva, verificando campo exacto, cero POST y cero productos hasta pulsar Registrar. Después abordar el aviso inmediato de duplicado de HU-PROD-03/CA02, que sigue previsto.

[Evidencia física](evidencias/03-K-physical-20261110T175820924988Z/physical.json) · [Persistencia](evidencias/03-K-physical-20261110T175820924988Z/orm-final.json).


## Continuación 03-K3 · perfil aplicado, prueba física en espera

Se observó un dispositivo conectado y la lectura 00CAT03K en Barcode to PC Server. La plantilla seleccionada Output template 1 contenía BARCODE y ENTER. La licencia rechazó crear otra plantilla por su límite, por lo que se editó la existente, retirando ENTER, y se aplicó el cambio. Guardar y aplicar quedó deshabilitado tras guardar. El nuevo ensayo aislado sigue esperando entrada del teléfono. La ausencia de POST con el campo vacío todavía no acredita el resultado después de leer.

Cursor vigente 03-K3 / PROP-03G-SCAN-T01. Escanear 00CAT03K en la ventana preparada y cotejar campo exacto, cero Enter, cero POST y cero productos. [Perfil observado y cambio](evidencias/03-K-physical-20261110T180229612612Z/profile.json).


## Resultado físico 03-K3

El operador confirmó el escaneo. A las 13:06:40 Lima llegó 00CAT03K completo, seguido de Enter, un POST y una ficha guardada en la base aislada. La ausencia de guardado automático INCUMPLE en este intento. Se volvió a observar la configuración del servidor y mostraba solo BARCODE con Guardar y aplicar deshabilitado. Posible plantilla anterior en móvil o sesión, hipótesis pendiente. Se solicitó reabrir la app móvil y crear sesión nueva antes de repetir. Se conservó la evidencia y el servidor Django terminó, con archivos protegidos intactos.

Cursor vigente **03-K4 / PROP-03G-SCAN-T01**, repetir después de reabrir app y sesión del teléfono. [Eventos](evidencias/03-K-physical-20261110T180229612612Z/physical.json) · [Datos finales](evidencias/03-K-physical-20261110T180229612612Z/orm-final.json).

## Continuación 03-K4 · perfil y lecturas repetidas

10/11/2026, America/Lima. Se comprobó por la interfaz de Barcode to PC Server un dispositivo conectado y el registro 00CAT03K. La plantilla Output template 1 tenía BARCODE y ENTER. Al alcanzar el límite de plantillas de la licencia, se ajustó la existente a solo BARCODE y se guardó. La primera repetición posterior conservó Enter y produjo una ficha aislada. El servidor seguía mostrando solo BARCODE. Después, el usuario confirmó haber reabierto la app móvil y creado una sesión nueva.

Las dos repeticiones siguientes registraron cero Enter, cero Tab, cero POST y cero productos. El control de guardado automático CUMPLE en esas muestras. La primera terminó con 32 caracteres, cuyo contenido exacto no se retuvo. La última registró primero el valor exacto 00CAT03K y terminó con 16 caracteres, confirmados por comparación como dos copias consecutivas de la etiqueta. El resultado final fue 00CAT03K00CAT03K. La hipótesis de configuración antigua en el móvil es compatible con el cambio observado tras reiniciarlo, pero no se inspeccionó el estado interno del teléfono.

HU-PROD-03/CA01 tiene evidencia de recepción física de código completo con ceros iniciales. La captura final de una única etiqueta queda PARCIAL por acumulación de lecturas. El lector se comporta como teclado y añade al campo enfocado. No se alteró la normalización de códigos para recortar repeticiones, ya que una cadena repetida podría ser un identificador legítimo.

**PROP-03K-RELECTURA, propuesta de criterio y tarea operativa.** Dado ADMIN registrando o corrigiendo un código, cuando realiza una lectura individual sobre el campo vacío o con su valor completo seleccionado, entonces debe quedar exactamente el texto de esa etiqueta. Ante repetición accidental, el operador debe poder reemplazar la captura y revisar el texto antes de guardar. Tarea pendiente de configurar y verificar el modo de lectura individual en la app móvil. Una opción de reemplazo automático en el formulario requiere definir cómo distinguir lectura de escritura manual y conservar códigos legítimos. No se implementó una deduplicación automática.

**Pruebas propuestas.** Leer una sola vez con cámara retirada después de capturar. Repetir con selección completa del valor previo. Probar dos etiquetas distintas y dos lecturas iguales. Verificar el código final, ausencia de envío, guardado expreso y rechazo atómico de código existente. HU-PROD-03/CA02, aviso inmediato de duplicado al leer, sigue previsto y pendiente de selección de implementación.

**Cursor vigente 03-K5 / PROP-03K-RELECTURA.** En la app móvil comprobar el modo individual y repetir con una sola lectura. Después comprobar reemplazo explícito seleccionando todo el campo antes de leer nuevamente. Concluir el guardado manual y consulta de la ficha entre roles en una base nueva. El funcionamiento sin Enter ya tiene dos muestras y se conserva como resultado del perfil aplicado.

Los tres servidores Django terminaron. Sus resultados confirman conservación de las bases protegidas y del XLSX. Las dos últimas bases conservaron toda la instantánea comercial, incluyendo cero productos. El programa del lector queda configurado con solo BARCODE en la plantilla existente. PostgreSQL y suite global no se repitieron, dado que este corte cambió la configuración externa y el soporte de observación. Las demás etapas mantienen su estado documentado.


[Detalle de evidencia](anexos/ETAPA-03-K4-perfil-y-relectura.md).

## Continuación 03-K5 · captura individual y alta explícita

10/11/2026, 13:14–13:16 Lima. El usuario aclaró que la versión móvil ofrece cámara y un botón de captura, sin opción visible Single scan. Esta interacción es suficiente para la prueba. En la base nueva el código físico 00CAT03K llegó con ocho eventos de entrada y dos ceros iniciales. Hasta confirmar el operador hubo cero Enter, cero Tab, cero POST y cero productos. Después de la confirmación humana, el soporte de auditoría pulsó explícitamente Registrar producto, observó la página de alta y comprobó un producto persistido con el código exacto. Se verificó así la separación temporal entre captura y guardado mediante acciones normales del formulario.

ALMACENERO entró desde Catálogo de productos y vio Higiene, precio 8,50, mínimo 10, cero unidades y Sin stock vigente, sin botones de gestión. VENDEDOR entró desde Preparar venta, con turno propio abierto, y buscó el código. La ficha sin stock no se ofreció. El servidor terminó y las bases protegidas y XLSX conservaron su hash. Las capturas y los registros JSON permiten reproducir y verificar estas observaciones. El clic de guardado lo ejecutó la automatización después de confirmar la captura física el usuario.

HU-PROD-03/CA01 CUMPLE en esta muestra de captura física y alta. El control de guardado explícito CUMPLE muestra. El usuario puede tomar varias capturas del mismo código. Se acreditó anteriormente que se concatenan en el campo enfocado. Releer con el campo vacío o su texto completo seleccionado evita añadir al valor previo. El reemplazo mediante una segunda lectura física queda NO EJECUTADO. La cadena concatenada puede cumplir el formato y ser única, por lo que no debe suponerse que la validación de duplicados la detectará como error de lectura. Ese riesgo se mantiene en PROP-03K-RELECTURA.

Cursor vigente **03-K6 / PROP-03K-RELECTURA**. Definir y verificar la interacción de reemplazo ante una segunda captura, conservando códigos legítimos y entrada manual. HU-PROD-03/CA02 sigue pendiente de selección e implementación de aviso inmediato al leer. La auditoría no modificó el código de la aplicación durante este corte. La planificación conserva los 27 CA base con 21 del alcance implementado que cumplen en muestras y seis previstos, uno de estos últimos con evidencia física favorable de CA01. Los cuatro criterios suplementarios de categoría conservan su evidencia previa.


[Evidencia física y guardado](evidencias/03-K-physical-20261110T181416503086Z/physical.json) · [Persistencia final](evidencias/03-K-physical-20261110T181416503086Z/orm-final.json).

## Continuación 03-K6 · lecturas repetidas

10/11/2026, America/Lima. El usuario pidió repetir lecturas del mismo código y solucionar su acumulación. La cámara informó 19 lecturas en la primera prueba. El campo acumuló ocho copias y llegó a su límite de 64 caracteres. No hubo envío ni altas.

Se configuró la plantilla existente del lector con PRESS KEY Ctrl+A seguido de BARCODE. No incluye Enter. Tras reiniciar la app móvil y abrir sesión nueva, se observaron 35 eventos Ctrl+A en el campo y 35 llegadas completas del código 00CAT03K. La longitud máxima observada fue ocho caracteres. Antes de confirmar, el campo contenía exactamente el código y existían cero POST y cero productos. Después de la confirmación del usuario, el soporte pulsó Registrar y persistió una ficha con ese código. ALMACENERO la consultó sin acciones de edición y con cero existencias. VENDEDOR no la encontró entre productos ofrecidos para venta. El servidor Django terminó y las bases protegidas y XLSX conservaron sus hashes.

**PROP-03K-RELECTURA CUMPLE en esta muestra física del formulario de alta.** Cada lectura reemplazó la anterior bajo la configuración probada. El lector actúa sobre el elemento que tiene el foco y Ctrl+A selecciona su contenido completo. Por tanto, la configuración también sustituye el texto de cualquier otro campo o aplicación que esté enfocado al leer. Su uso exige enfocar el campo destinado a recibir el código. La licencia solo permitió una plantilla, por lo que el ajuste se aplicó a Output template 1 y afecta a sus demás usos. Para revertirlo se retira PRESS KEY y se guarda la plantilla.

No se probaron una segunda etiqueta diferente, edición de ficha ni un flujo de venta con el lector. El aviso inmediato de duplicados de HU-PROD-03/CA02 sigue previsto. **Cursor 03-K7 / PROP-03K-RELECTURA.** Verificar reemplazo con dos etiquetas diferentes en alta y edición, foco correcto, captura manual y rechazo final de un código existente. Después revisar el alcance del aviso inmediato de duplicado.


[Evidencia de relecturas](evidencias/03-K-physical-20261110T182622655374Z/physical.json).

## Continuación 03-K7 y 03-K8 · Ediciones y foco de lectura

**K7.** Dos pantallas de la misma ficha permitían que la segunda restaurara un precio antiguo al guardar otro campo. Se corrigió el guardado y se verificó la recuperación en Chrome con dos ADMIN. El catálogo y el mostrador reflejaron el precio vigente. Pasaron 318 métodos Django, 32 comprobaciones en Chrome, tres carreras en SQLite y dos en PostgreSQL. Dos observaciones de Chrome reproducen el riesgo de escanear sobre Nombre. [Matriz y evidencia antes/después](anexos/ETAPA-03-K7-edicion-y-relectura.md).

**K8.** ADMIN puede abrir «Escanear código», revisar las lecturas en un campo temporal, copiar la elegida a la ficha y guardar expresamente. Mientras el diálogo está abierto, una relectura solo cambia la captura. Se observaron 41/41 comprobaciones de teclado emulado en Chrome, entre ellas dos códigos distintos, lectura repetida, exceso de longitud, cancelación, edición, duplicado, inventario e histórico conservado, consulta de ambos roles y alta manual sin JavaScript. El riesgo de escribir en otro campo persiste fuera de este modo. [Matriz, capturas y reproducción](anexos/ETAPA-03-K8-captura.md).

**Cobertura y traspaso.** Se mantienen 9 HU y 27 CA base, más los cuatro suplementarios de categoría. HU-PROD-03 sigue en el backlog futuro, con evidencia parcial de la funcionalidad y aviso inmediato de duplicados pendiente. Los ensayos del lector en catálogo no ejercitan recepción de paquetes. Se documentan tres historias propuestas y once pruebas integrales por ejecutar, incluidas idempotencia de recepción, dos almaceneros, daño parcial, vencimiento, defecto de fábrica, cuarentena y retiro selectivo por lote. El diseño prevé asociar cada línea de venta con los lotes consumidos. El cobro inspeccionado descuenta los lotes pero no registra esa asociación, brecha que debe probarse sobre una venta de dos lotes en 11/12/14 y evaluarse en 16. [Cobertura de recepción y retiros](anexos/ETAPA-03-recepcion-y-retiros-pendientes.md).

## Continuación 03-K9 · Dos etiquetas físicas en la ficha de catálogo

10/11/2026, 20:18–20:20 Lima. Chrome 157, servidor web local aislado, Barcode to PC Server y teléfono del operador. Con el diálogo «Escanear código» activo, el operador escaneó las etiquetas y confirmó cada uno de los cinco pasos en Chrome. El soporte mostró una sola etiqueta por vez, observó las entradas y pulsó «Usar código» y el guardado ordinario únicamente tras la confirmación que autorizaba esa operación. Las etiquetas no se introdujeron por automatización.

| ADMIN, HU-PROD-02/03/04 | Lecturas completas de Code 128 | Resultado observado |
|---|---|---|
| Alta, selección A → B | 6 de A y 7 de B | Un solo POST expreso. Se creó una ficha nueva con B, UND, precio S/ 8,50 y mínimo 10. |
| Edición de una ficha con venta previa, B → A | 7 de B y 6 de A | Un solo POST expreso. Se conservó la identidad de la ficha y la venta anterior retuvo su código original. El alta con B y la tercera ficha conservaron sus datos. |
| Intento de asignar B a la ficha con A | 7 de B | Un solo POST expreso. El servidor mostró «Ya existe un producto con este código de barras.» y la instantánea posterior coincidió con la previa al intento. |

**PROP-03K-RELECTURA CUMPLE en esta muestra física.** Los identificadores fueron `00CAT03K-A` y `00CAT03K-B`. Hubo 33 Ctrl+A, 330 eventos de entrada, 33 llegadas completas, longitud máxima de 10, cero entradas en otros campos y cero Enter/Tab. Antes de usar el código y guardar se cotejaron formulario y base. Se verificaron 38/38 comprobaciones, incluida la conservación de los campos inventariados del lote, turno, venta, línea de venta y borradores. Las consultas de ALMACENERO y VENDEDOR fueron ejercitadas en K7/K8. La protección de foco requiere mantener activo el diálogo. HU-PROD-03/CA02, aviso al leer un duplicado, conserva su clasificación futura. [Registro de lecturas](evidencias/03-K-phone-20261111T011843801709Z/phone.json) · [Antes](evidencias/03-K-phone-20261111T011843801709Z/orm-initial.json) · [Después](evidencias/03-K-phone-20261111T011843801709Z/orm-final.json).

**Reproducción.** Con el teléfono conectado, ejecutar desde la raíz `& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' phone`. En Chrome seguir las cinco etiquetas y sus botones de confirmación. El soporte crea una base exclusiva, abre el diálogo y da cuatro minutos para las lecturas. El servidor Django de este ensayo se cerró. La base original y las bases protegidas anteriores presentes conservaron sus hashes. El XLSX seguía ausente al iniciar la corrida. [Cierre](evidencias/03-K-phone-20261111T011843801709Z/result.json).

**Siguiente cursor 03-L / HU-CAT-02 (estado suplementario) / HU-PROD-05, frontera con venta.** Crear una categoría activa, ficha activa, lote vigente con 20 unidades y borrador de dos unidades con turno OPEN. En un PostgreSQL aislado, sincronizar la desactivación confirmada por ADMIN con el cobro del VENDEDOR y reproducir ambos órdenes de confirmación. Si la suspensión ya quedó confirmada al evaluar el cobro, exigir rechazo con borrador, saldo e histórico íntegros. Si la venta ganó primero, verificar una única venta de dos unidades y bloqueo para la siguiente operación. Registrar la espera y los saldos. Después, repetir la frontera con una entrada de ALMACENERO. Ambas carreras permanecen **NO EJECUTADAS**. La recepción de paquetes y los retiros conservan los once casos pendientes en su [anexo](anexos/ETAPA-03-recepcion-y-retiros-pendientes.md).

**Corte 03-L, 10/11/2026.** Si la suspensión de categoría gana, cobro y entrada rechazan sin efectos comerciales. Si la operación gana, confirma una sola vez y la suspensión bloquea la siguiente. Verificados con espera real en PostgreSQL y formularios antiguos en Chrome. Los servicios existentes cumplieron las muestras. El cursor siguiente es 03-M, suspensión de producto individual. [Inventario, resultados, reproducción y límites](anexos/ETAPA-03-L-suspension-con-operaciones.md).

**Corte03-M,10/11/2026.** Cuatro carreras reales y27 comprobaciones de navegador verifican la suspensión individual contra cobro y entrada, con otra ficha de la misma categoría como control. No cambió código funcional. Dos fallos del soporte de navegador se conservaron y corrigieron antes de repetir. Siguiente cursor03-N:reclasificación,HU-PROD-04/CA05. [Inventario, resultados, propuestas y límites](anexos/ETAPA-03-M-producto-con-operaciones.md).

**Corte03-N/O,10/11/2026.** Se seleccionó el aviso pendiente por la petición de aplicar mejoras: HU-PROD-03/CA02 ahora consulta unicidad antes de copiar y conserva validación definitiva al guardar. Reclasificación verificada con rechazo íntegro y reintento cuando compite con cobro. Los intentos fallidos y correcciones del soporte se conservan. [Matriz, cambios, pruebas y cursor](anexos/ETAPA-03-N-O-reclasificacion-y-duplicados.md).

## Continuación 03-P · Aviso físico y ensayo de migraciones

**Etapa 03 hasta 03-P.** Aviso de duplicados verificado con teléfono: cinco fases, 34 lecturas y 52/52 comprobaciones; una alta expresa y cero envíos automáticos. Migraciones catalog0003–0006 aplicadas solo en copia nueva, datos comerciales comparados conservados; 18/18 regresiones acotadas. Base original intacta. Despliegue y recepción/retiros integrales pendientes. Cursor **03-Q / HU-PROD-04 CA05 / AUD03Q-CONC01**, reclasificación cruzada y borrador multiproducto en PostgreSQL aislado. [Detalle](anexos/ETAPA-03-P-aviso-fisico-y-migraciones.md).

No hubo cambios funcionales nuevos. Se conservaron cambios preexistentes y se añadieron soportes de prueba. La copia de migraciones no se expuso por navegador ni sustituye la base original. Recepción/retiros y otras etapas mantienen sus estados. Ver inventario del sublote, evidencia, limitaciones y reproducción en el anexo enlazado.

## Continuación 03-Q · Reclasificación cruzada

**Etapa 03 hasta 03-Q.** Se reprodujo un interbloqueo PostgreSQL entre reclasificación y cobro multiproducto; corregido orden de bloqueos y snapshots. Resultado final: 5/5 escenarios PG, regresiones L/M/N 4/4 cada una, 27/27 comprobaciones Chrome secuenciales y 326/326 métodos. Base original intacta. Próximo cursor **03-R / AUD03R-PRECIO-CONC01**, rama de actualización de precios bajo concurrencia. Despliegue y recepción/retiros siguen pendientes. [Detalle](anexos/ETAPA-03-Q-reclasificacion-cruzada.md).

La corrección afecta `sales/services.py`; los detalles del deadlock, ejecución antes/después, casos, traspaso y límites constan en el anexo. Las secciones anteriores conservan cursores históricos.

## Continuación 03-R · Precio y resumen de cobro

**Etapa 03 hasta 03-R.** Tres carreras PostgreSQL de refresco de precio pasaron; se corrigió la aceptación de cobro al omitir controles del resumen. Resultado final: 3/3 PG, 27/27 navegador de precio, 6/6 petición alterada y 328/328 métodos. Base original intacta. Próximo cursor **03-S / AUD03S-RESUMEN-CONC01**, comparación del resumen frente a cambios concurrentes. Despliegue y recepción/retiros siguen pendientes. [Detalle](anexos/ETAPA-03-R-precios-y-resumen.md).

La corrección de omisión afecta `sales/views.py`; la prueba de carreras afecta solo la frontera de venta. La comparación vista-servicio aún no se ha probado atómicamente. Ver anexo para evidencia, límites y reproducción.

## Continuación 03-S · Resumen y cobro atómicos

**Etapa 03 hasta 03-S.** Se reprodujo y corrigió el cobro de un borrador cambiado después de revisar el resumen, incluso con igual subtotal. Resultado: 3/3 casos PG, 23/23 navegador secuencial, 20/20 regresiones PG Q/R/L/M/N y 332/332 métodos. Base original intacta. Cursor **03-T / AUD03T-CATALOGO-RESUMEN01**, cambio de nombre/código durante confirmación web. Despliegue y recepción/retiros pendientes. [Detalle](anexos/ETAPA-03-S-resumen-atomico.md).

La vista transmite el resumen revisado al servicio y este lo contrasta bajo bloqueo en las dos ramas. Llamadas internas sin resumen conservan compatibilidad; serialización no autenticada. Ver anexo para evidencia, límites y reproducción.

## Continuación 03-T · Catálogo y resumen

**Etapa 03 hasta 03-T.** Cambio concurrente de nombre/código exige revisión; reclasificación entre categorías activas conserva el resumen visible. 3/3 casos PG y 28/28 comprobaciones secuenciales Chrome; mensaje impreciso corregido y 332/332 métodos. Base original intacta. Cursor **03-U / AUD03U-CATEGORIA-VENTA01**, reclasificación y suspensión de categoría frente a cobro multiproducto. Despliegue y recepción/retiros pendientes. [Detalle](anexos/ETAPA-03-T-catalogo-y-resumen.md).

El cambio de mensaje está en `sales/views.py`. La prueba PG usa Django test Client; la del navegador fue secuencial. Ver el anexo para resultados, límites y reproducción.

## Continuación 03-U · Categoría y cobro

**Etapa 03 hasta 03-U.** Tras reclasificar P, suspensión de categoría y cobro multiproducto pasaron 2/2 órdenes PostgreSQL; recorrido secuencial entre roles pasó 35/35 comprobaciones. Sin cambio funcional; base original intacta. Cursor **03-V / AUD03V-TRIPLE-CATEGORIA01**, tres operaciones simultáneas. Despliegue y recepción/retiros pendientes. [Detalle](anexos/ETAPA-03-U-categoria-y-cobro.md).

El navegador fue secuencial y la reclasificación precedió a la carrera PostgreSQL. Ver anexo para resultados, alternativas, límites y reproducción.

## Continuación 03-V · Concurso triple

**Etapa 03 hasta 03-V.** Reclasificación, suspensión y cobro multiproducto pasaron 3/3 intercalaciones PostgreSQL con tres conexiones; sin cambios funcionales. Navegador secuencial sigue en03-U. Base original intacta. Cursor **03-W / AUD03W-CONCILIACION-CATALOGO01**, conciliación de inventario y pendientes. Despliegue y recepción/retiros pendientes. [Detalle](anexos/ETAPA-03-V-concurrencia-triple.md).

La prueba usó servicios reales en tres conexiones; no usó vista web ni navegador nuevo. Ver anexo para intercalaciones, límites y reproducción.

## Continuación 03-W · Conciliación vigente

**Etapa 03 hasta 03-W.** Conciliados 27 criterios base y cuatro suplementarios: 23 CUMPLE en muestras del alcance vigente y 4 futuros; existe discrepancia de redacción entre CA01 original del lector y su adenda de copia expresa. Mapa actual: 12 rutas/9 plantillas, incluidas vencimientos→07. Base original intacta. Cursor **03-X / AUD03X-CODIGO-EAN-UPC01**; despliegue y recepción/retiros pendientes. [Matriz vigente](anexos/ETAPA-03-W-conciliacion.md).

Se corrigieron recuentos y se distinguieron adendas históricas de la situación actual; no hubo nuevas pruebas funcionales, cambios de aplicación ni modificación de bases.

## Continuación 03-X · EAN/UPC

Actualización11/11/2026; ejecución10/11,23:00–23:04 Lima. **Etapa 03 hasta 03-X.** 69/69 controles navegador/HTTP/ORM,16/16 de servicio/DB y9/9 de observación física. El teléfono entregó UPC12 para la etiqueta EAN13 almacenada; la consulta no lo reconoció como duplicado. **PROD03/CA02 PARCIAL** en esta frontera:22 CA CUMPLE en muestras,1 PARCIAL y4 futuros;4 suplementarios conservan sus muestras. Base original intacta; política de identidad, despliegue y recepción/retiros pendientes. **Cursor03-Y / AUD03Y-PREFLIGHT-IDENTIDAD01**. [Evidencia y alternativas](anexos/ETAPA-03-X-codigos-ean-upc.md).

## Continuación 03-Y · Identidad de producto y relecturas

**Etapa 03 hasta 03-Y.** El alta exige distinguir GTIN de fabricante y código interno. En Chrome, la lectura UPC12 de la etiqueta registrada con EAN13 mostró el aviso de duplicado y bloqueó la copia. Las pruebas abarcaron 47 controles de navegador/servidor, 9 de lectura física, 4 escenarios concurrentes y 335 métodos de regresión. Balance de 27 criterios base: 23 CUMPLE en las muestras y 4 previstos (CAT03/04). Quedan cuatro suplementarios con sus muestras previas. [Informe y evidencia](anexos/ETAPA-03-Y-identidad.md).

**03-Z / AUD03Z-RELECTURA-INTERNA01**. En Chrome aislado, seleccionar código interno y reproducir una secuencia delimitada con Ctrl+A en la que llegan concatenadas dos lecturas iguales y dos distintas. Contrastar con un código interno legítimo de patrón repetido. Verificar el valor temporal, la confirmación de copia, el POST y el estado comercial antes/después. Después, PROD04/CA03: probar por navegador dos fichas antiguas con representaciones solapadas e históricos, y una tercera sin solapamiento.

## Continuación 03-Z · Códigos internos y fichas antiguas

**Etapa 03 hasta 03-Z.** Se corrigió la concatenación de códigos internos al perderse la selección después de Ctrl+A. Chrome y el teléfono verificaron la sustitución de A por B. En edición, dos fichas antiguas con variantes solapadas conservaron sus lotes y ventas tras el rechazo. Una tercera pudo clasificarse. 34 comprobaciones automatizadas de navegador y 335 métodos de regresión aprobados. Balance de 27 criterios base: 23 CUMPLE en muestras y 4 previstos de CAT03/04. Los cuatro suplementarios conservan sus muestras. [Informe, pruebas y límites](anexos/ETAPA-03-Z-relectura-interna.md).

**03-AA / PROP-03-RET-T01, frontera catálogo–recepción**. Con tres artículos ficticios y un paquete de 12, contrastar el código exterior con el de unidad, identificar la ficha en las consultas autorizadas y verificar que la consulta por sí sola conserva los saldos. Trasladar el registro por proveedor, cantidad, lote y vencimiento a 05–06.

## Continuación 03-AA · Código exterior y consulta de unidades

**PROP-03-RET-T01 PARCIAL y frontera PROD01/CA02 CUMPLE en la muestra.** Se prepararon tres artículos, seis lotes vigentes y tres ventas ficticias. El supuesto del ensayo fue una caja de 12 unidades de A con código exterior distinto. La cantidad 12 pertenece al escenario y no es un dato contenido en la lectura. A, B y C quedaron con 6, 7 y 8 unidades tras las ventas de preparación. En Chrome, ALMACENERO y VENDEDOR consultaron A, B, la variante de A, C y el código exterior. Cada consulta de unidad devolvió únicamente la ficha y saldo esperados. Ante la caja, el catálogo y la consulta de venta mostraron que no había coincidencias. La comprobación de códigos de ADMIN rechazó el exterior como GTIN de artículo unitario. Cero POST en las búsquedas e instantáneas comerciales idénticas. Se ejecutaron 36/36 comprobaciones. La creación de movimientos de recepción quedó fuera del ensayo. No se utilizó un paquete físico.

Reproducir desde la raíz con `r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03y_browser_run.py aa-box`. [Inventario inicial](evidencias/03-AA-aa-box-20261111T165403451847Z-71d9a79a/inventory-before.json) · [Ensayo de caja y unidad](evidencias/03-AA-aa-box-20261111T165403451847Z-71d9a79a/browser.json) · [Cierre verificado](evidencias/03-AA-aa-box-20261111T165403451847Z-71d9a79a/result.json).

**PROP-03-RET-T01 / HU-INV-01a y HU-INV-01b (05–06)**. En recepción aislada por ALMACENERO, presentar tres productos y varios lotes, identificar una caja de 12 con código exterior desconocido, contrastar las unidades confirmadas por el operador y verificar proveedor, costo, vencimiento, saldo al recargar y efecto de cancelar o repetir. Inventariar primero las rutas de recepción. Mantener cuarentena y retiro por lote en su traspaso 07–08/16.

## Continuación 03-AB · Frontera de recepción por producto

**Continuación 03-AB, con evidencia parcial de 05-A y 06-A.** Se verificaron tres recepciones por producto y una reposición, cancelación, reenvío y consultas entre roles. Se corrigieron límites de validación del servicio y textos de recepción. Pasaron 79 comprobaciones de Chrome, tres carreras PostgreSQL y337 métodos de regresión. El catálogo conserva23 de27 criterios base CUMPLE en muestras y4 futuros, más cuatro suplementarios previos. [Evidencia del corte](anexos/ETAPA-03-AB-recepcion.md).

Se emplearon tres operaciones independientes por producto, cada una con varios lotes. La recepción multiproducto en una sola operación y las tareas integrales de retiro siguen pendientes. **05-B / INV-01a-CA02 y PROP-03-RET-T04/T06**. Abrir recepción con proveedor activo, desactivarlo desde otra sesión y confirmar. Comprobar revalidación en servicio y carrera PostgreSQL, rechazo completo y mensaje. Después completar fronteras de fecha en Lima e inmutabilidad del ingreso. RN-01 frente a entrada directa mantiene decisión pendiente en06.

## Continuación 03-AC · Proveedor y vencimientos

**Continuación 03-AC / 05-B, frontera compartida con06.** Se corrigió la recepción con un proveedor cuya instancia había quedado obsoleta y el límite de vencimiento anunciado de20 años. Pasaron29 controles de Chrome, cuatro carreras PostgreSQL y343 métodos de regresión. Catálogo conserva23/27 criterios base CUMPLE en muestras y4 futuros, más cuatro suplementarios previos. [Hallazgos y evidencia](anexos/ETAPA-03-AC-proveedor-y-fechas.md).

**05-C / HU-INV-01a-CA05 y RN-19**. Preparar empates de vencimiento, fecha de ingreso y UUID. Verificar edición del instante de ingreso y selección FEFO en una salida autorizada, conservando históricos. Mantener el cierre integral de venta, recepción multiproducto, cuarentena y retiros en sus etapas.

## Continuación 03-AD / 05-C

**Continuación 03-AD / 05-C.** Se protegió la fecha de ingreso del lote en modelo y base de datos. Se verificó FEFO por vencimiento, antigüedad y UUID, así como la exclusión de vencidos y un cobro simultáneo repetido. Pasaron24 controles Chrome y346 métodos de regresión. PostgreSQL aprobó tres casos. Migración ensayada en copia SQLite y PostgreSQL, despliegue pendiente. [Evidencia y límites](anexos/ETAPA-03-AD-fefo-e-ingreso.md).

**05-D / INV01a-CA01–03 y PROP-03-RET-T06**. Revisar evidencia03 previa y completar recepción contra desactivación de producto/categoría entre selección y confirmación, incluyendo órdenes concurrentes aún no cubiertos y conservación de saldo/costo. RN-01, recepción multiproducto indivisible y trazabilidad venta→lote para retiros siguen pendientes.


## Continuación 03-AE / 05-D

**Continuación 03-AE / 05-D.** La carga inicial rechazó productos o categorías desactivados desde otra sesión sin alterar lotes ni costos; la reactivación permitió una carga y su consulta por vendedor. Pasaron 29 comprobaciones Chrome y cuatro carreras PostgreSQL con bloqueo observado. Sin cambios funcionales nuevos. [Evidencia, cobertura y límites](anexos/ETAPA-03-AE-carga-y-disponibilidad.md).

**05-E / AUD05E-CONCILIACION-INV01a**, consolidar los cinco criterios de carga inicial y PROP-03-RET-T01–T06/T11 contra evidencias03-AB–AE y03-L/M; separar muestras ejecutadas, recuperación ante respuesta incierta y decisiones de recepción multiproducto. Resolver documentalmente qué falta para cerrar05, manteniendo RN-01 en06 y trazabilidad/retirada en07–08/11–12/16. No repetir pruebas aprobadas sin un cambio o una brecha concreta.


## Continuación 03-AF / 05-E

**Continuación 03-AF / 05-E.** Conciliados los cinco criterios de carga inicial con sus evidencias. Se añadieron 38 comprobaciones Chrome: pérdida simulada de respuesta antes/después de guardar, reintento sin duplicación, recuperación de constancia, redondeo HALF_UP y permisos de sus dos rutas. Se alineó la descripción de INV-01a con DOC03-01. Sin cambios funcionales nuevos. [Matriz, pruebas y pendientes](anexos/ETAPA-03-AF-conciliacion-carga.md).

**06-B / HU-INV-01b-CA02 y RN-28, frontera con11.** Preparar producto con dos lotes, vender unidades y guardar constancia/estado; registrar reposición que cambie el costo promedio y comprobar si cada venta conserva el costo aplicable al cobrar. Reproducir primero la brecha de03-Q en navegador y persistencia. Corregir únicamente el defecto inequívoco; no inventar costos de ventas antiguas. RN-01/DOC-03AB-01 mantiene su decisión independiente. Recepción multiproducto, caída de servidor, cuarentena y retiro siguen pendientes en sus traspasos.


## Continuación 03-AG / 06-B

**Continuación 03-AG / 06-B.** Reposición y costo histórico verificados: corregidos el costo ausente del detalle de venta y el promedio posterior a FEFO. 12 controles finales Chrome, 3 casos PostgreSQL y350/350 métodos. Migración ensayada en copia SQLite y PostgreSQL, original intacto. Ventas antiguas conservan costo desconocidoNULL. [Detalle y evidencia](anexos/ETAPA-03-AG-costo-historico.md).

**03-AH / 06-C / AUD03AH-COSTO-VENCIDOS01.** Dos lotes con costos y vencimientos distintos: vender por FEFO, avanzar fecha hasta vencer uno y reponer; contrastar stock físico/vigente y valoración con RN14/BUG005. Después merma/ajuste y conservación de costos históricos. RN01, despliegue y retiro sanitario siguen pendientes; no cerrar otros módulos.


## Continuación 03-AH / 06-C

**Continuación 03-AH / 06-C.** 30 comprobaciones Chrome y6 regresiones acotadas. Se reprodujo cambio de costo4.50→5.00 al retirar una unidad vencida sin cambiar existencias vendibles; ventas previas conservaron3.0000. **DOC-03AH-01 pendiente:** conciliar promedio móvil con recálculo por lotes. Sin cambios funcionales. [Informe y alternativas](anexos/ETAPA-03-AH-valoracion-vencidos.md).

**03-AI / 06-D / AUD03AI-REPOSICION-RESPUESTA01.** Probar pérdida de respuesta antes/después del commit de una reposición, reenvío y recuperación por inventario/constancia; comprobar lotes, cantidades, costo y responsable. DOC-03AH-01 queda pendiente sin bloquear esta prueba. Despliegue y retiro sanitario pendientes.


## Continuación 03-AI / 06-D

**Continuación 03-AI / 06-D.** 57 comprobaciones Chrome/HTTP/ORM y 6 regresiones. Pérdida de respuesta antes/después del commit y reenvíos sin duplicación en la muestra; recuperación por ficha acumulada. Cinco denegaciones de roles comprobadas con CSRF válido. Sin cambios funcionales. [Evidencia y límites](anexos/ETAPA-03-AI-reposicion-respuesta.md).

**03-AJ / 06-E / AUD03AJ-SESION-RECEPCION01.** Confirmar formulario antiguo tras invalidar sesión ALMACENERO; verificar rechazo sin escritura, reautenticación y recuperación. Después cambio de rol/desactivación con CSRF válido. DOC-03AH-01 y DOC-03AI-01 abiertos; despliegue y retiro sanitario pendientes.


## Continuación 03-AJ / 06-E

**Continuación 03-AJ / 06-E.** Sublote completado sobre sesión vencida en BD, cierre en pestaña paralela, rotación de CSRF, `?next=` con rol `ADMIN`, cambio de rol a `VENDEDOR` y desactivación/reactivación de cuenta en `/inventario/entrada/`. Corregidos `H-03AJ-01` (`_lock_warehouse_actor` con `select_for_update()` sobre `Account` en `confirm_initial_load` y `register_stock_entry`), `H-03AJ-02` (`logout(request)` ante sesión inactiva en `roles_required`, `login_view` y `dashboard`) y `H-03AJ-03` (`@never_cache` en vistas de carga/entrada y `.form-panel.load-detail-panel` en ficha de existencias confirmadas). Conservados el corte visual previo (`135b54cf`, 32/32), el primer intento de pruebas Django (`15` métodos, `4` fallos) y dos corridas Chrome interrumpidas en paso 23 (`e8bd3f5c`, `b9cc3ea9`). Verificación final válida tras los últimos cambios: **46/46** Chrome/HTTP/ORM, **6/6** carreras PostgreSQL 18.4 (`pg_blocking_pids` sobre `identity_account`), **15/15** pruebas acotadas y **362/362** pruebas completas de las 6 aplicaciones (`AUDIT03K_DEFAULT_COOKIES='1'`). La frontera transversal en `write_off_stock`, `register_physical_adjustment` y `_require_seller` no se modificó por corresponder a Etapas `08`/`10`/`11`. Catálogo conserva 23/27 CA base `CUMPLE` en muestras del alcance vigente, 4 futuros (`CAT-03/04`) y 4 suplementarios previos. Base original y bases protegidas conservan SHA-256. [Detalle, capturas e índice](anexos/ETAPA-03-AJ-sesion-recepcion.md) · [`03-AJ-indice.json`](evidencias/03-AJ-indice.json).

**06-F / AUD06F-CONCILIACION-INV01b.** Conciliar `HU-INV-01b/CA-01..02` y `RN-01/14/28/29` frente a `03-AG`, `03-AH`, `03-AI` y `03-AJ`, dejando trazado el estado por criterio y las alternativas abiertas (`DOC-03AB-01`, `DOC-03AH-01`, `DOC-03AI-01`) antes de pasar a Etapa 04 (`HU-PROV-01/CA-01`) o Etapa 07 (`HU-PROD-06/CA-01`). Despliegue de migraciones, caída real de servidor/BD, recepción multiproducto indivisible, cuarentena y retiro sanitario permanecen pendientes; no cerrar otras etapas (`04`–`17`).
