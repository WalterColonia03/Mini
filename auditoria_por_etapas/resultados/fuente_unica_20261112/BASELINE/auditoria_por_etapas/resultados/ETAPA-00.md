# Adenda vigente de ETAPA-00 · 12/11/2026

**Estado actual:** Inventario completo del corte, no aprobación funcional. **Pendientes compartidos:** DOC00-01/05/07/08/09/12/13; matriz219 y catálogo74+8. **Próximo cursor:** Revisión17 de trazabilidad y semántica.

[Mapa consolidado y decisiones](conciliacion_20261112/CONSOLIDACION.md) · [Contratos de implementación](conciliacion_20261112/ENCARGOS.md) · [Verificación integrada](conciliacion_20261112/VERIFICACION.md) · [Informe original íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ETAPA-00.md).

Las decisiones nuevas se aceptan desde12/11 por delegación explícita del usuario. No se cambia el resultado histórico de una muestra ni se declara cerrado el módulo. Requisitos recién revisados requieren nueva implementación/verificación. Las referencias de línea del texto histórico remiten a BASELINE. Los anexos conservan su fecha y vigencia original; los estados actuales se consultan en el mapa.

## Rectificaciones transversales aplicables

Etapa09 sí tiene ejecución/evidencia (Chrome67funcionales+1control), aunque10–12 y estado general antiguos la dejaban pendiente. 04-D acredita revocación en sus muestras; su límite raw sin petición/servicio permanece. El fallo `_state.adding` de inventario fue corregido05-L e incluido en434tests actuales. Los informes antiguos que lo separaban no prueban fallo actual. El empate de orden de turnos no se considera corregido por repetir una corrida. Soporte12PG es DjangoClient concurrente contraPG, no redHTTP por sockets. 05-Linterrupción antes de escribir no prueba caída postwrite. HU-VEN-05b pide filtrosCA02 y detalleCA03; no hay conflicto de líneas expandidas.

---

## Informe y resultados históricos conservados

# ETAPA 00 — Línea base, frontera del producto y entorno aislado

**Estado de la etapa 00: COMPLETADA en su alcance de inventario, frontera del producto y preparación de auditoría.** Sublotes 00-A, 00-B y 00-C terminados. Inicio 05/11/2026, cierre 09/11/2026, America/Lima. Las evaluaciones funcionales y las decisiones de alcance registradas tienen su siguiente caso asignado en las etapas 01–17.

## 1. Alcance y exclusiones

Se leyó completo `auditoria_por_etapas/PROTOCOLO_COMUN.md`. No existía `resultados/ESTADO_GENERAL.md` al iniciar. Se inventariaron fuentes y superficie del producto, con un único recorrido operativo acotado para comprobar que el entorno permite auditar: ingreso de tres roles, alta de un producto por ADMIN, consulta posterior por ALMACENERO y rechazo de VENDEDOR/visitante. No se intentó probar cada historia ni cada ruta superficialmente.

El inventario reúne identificadores de HU, CA, reglas y tareas con su fuente y alcance. Los índices de código y cobertura ubican las rutas, plantillas, permisos, campos, mensajes, acciones, salidas y métodos de prueba. El cierre 00-C expande los formularios propios, las condiciones de interfaz y el sitio administrativo. Los nueve grupos QA históricos cuentan con 30 afirmaciones trazables. Ocho criterios de la matriz individual remiten al comportamiento observado en 00-A y conservan estado PARCIAL. La comprobación sistemática de las variantes corresponde a la etapa funcional asignada.

No se ejecutaron semillas del proyecto, reset, limpieza, restauración, Jira, compras, ventas, caja, lotes, normativa ni concurrencia PostgreSQL. No se usaron datos reales. El libro de planificación no fue modificado ni usado como autoridad de aceptación.

## 2. Fuentes, clasificación y manifiestos

| Artefacto | Contenido y uso |
|---|---|
| [Índice de planificación](anexos/ETAPA-00-planificacion.md) / [JSON individual](anexos/ETAPA-00-planificacion.json) | 74 HU con 219 CA base; 8 ideas sin CA; 30 RN; 67 tareas; 41 CA de matriz R1; actor, fuente y dependencias por HU. |
| [Conflictos de planificación](anexos/ETAPA-00-conflictos-planificacion.md) | DOC-00-01..13, citas, alternativas y propuestas; no aceptación implícita. |
| [Agregados QA descompuestos](anexos/ETAPA-00-agregados-QA.md) | 30 afirmaciones localizadas en las nueve filas `08:869–877`; no son CA nuevos aceptados ni reemplazan los 219 CA base. |
| [Extras inversos](anexos/ETAPA-00-extras-inversos.md) | Descuento, estado de categoría, resumen y stock: UI, permisos, servidor, persistencia, pruebas candidatas, conflictos y propuestas adicionales. Análisis estático; NO EJECUTADO. |
| [Formularios generados](anexos/ETAPA-00-formularios-generados.md) / [JSON](anexos/ETAPA-00-formularios-generados.json) | 18 clases propias, 53 campos efectivos, formset de lotes y cuatro campos de gestión. Etiquetas, validadores, mensajes, widgets, límites y limpieza por campo. |
| [Superficie UI](anexos/ETAPA-00-superficie-ui.md) / [CSV](anexos/ETAPA-00-superficie-ui.csv) | 2.367 localizaciones de interfaz y servidor, con fuente, rol, ruta, condición, salida, candidato HU/RN y etapa. |
| [Administración y perímetro](anexos/ETAPA-00-admin-y-perimetro.md) / [JSON](anexos/ETAPA-00-admin-metadatos.json) | 65 patrones admin, nueve modelos registrados, inline y formularios técnicos. Incluye el manejo de estáticos fuera del resolver. |
| [Inventario de código](anexos/ETAPA-00-codigo.md) / [CSV de ocurrencias](anexos/ETAPA-00-inventario-codigo.csv) | 2.446 ocurrencias clasificadas por tipo, identificador, archivo y línea. Índice inverso desde código/UI hacia candidatos de planificación. |
| [Cobertura inicial](anexos/ETAPA-00-cobertura.md) / [CSV](anexos/ETAPA-00-cobertura.csv) | Matriz individual: 219 CA base + 9 grupos QA + 8 ideas, con tipos separados, estado y siguiente etapa. Los vínculos por módulo son candidatos, no pruebas de equivalencia. |
| [Fuentes y entorno documental](anexos/ETAPA-00-fuentes.md) | Papel/fecha/vigencia de documentos, históricos, archivos comprimidos, XLSX y cambios Git preexistentes. |
| [Resolver completo](evidencias/00-rutas-resueltas.json) | 106 patrones: 41 de negocio + 65 bajo `/admin/`, incluido catch-all. No son 106 pantallas ni solicitudes ejecutadas. |
| [Deriva de código](anexos/ETAPA-00-deriva-codigo-09nov.json) y [revalidación documental](anexos/ETAPA-00-fuentes-revalidacion-20261109.json) | 77 hashes de fuentes AST/HTML y 66 hashes de fuentes/documentos comparados sin cambios entre cortes; conjuntos superpuestos, no sumarlos. Revalidación documental repetida 09/11 10:12 Lima con el mismo resultado; su JSON se sobrescribió. 51 fuentes técnicas adicionales sin hash inicial. |

`r1-pmv` es la aplicación Django activa y el único repositorio Git encontrado en esta raíz. `qr-minimarket` contiene una imagen, no otra implementación. La raíz de planificación no es repositorio Git. Los cambios ya presentes en `r1-pmv` se conservaron; HEAD, lista de cambios y hashes constan en el anexo. La igualdad del estado Git no acredita igualdad de contenido de todo archivo no rastreado.

**03_Matriz_de_Trazabilidad_y_Pruebas.md es una matriz histórica de R1**, explícitamente en su línea 3, con 41 CA en la línea 7. No es la lista completa del producto. Los informes históricos con 95/126/152/163/202 pruebas, y las 191 pruebas declaradas por la guía 21:42, son ejecuciones ajenas a este sublote. La cifra 191 del inventario de código significa métodos `test_*` definidos; no se volvió a ejecutar esa suite.

El libro de planificación conserva el estado declarado en su corte de tres sprints. Se verificaron sus identificadores y 97 ordinales de criterio, junto con las discrepancias de vigencia de AUTH-02 y USR-05. La hoja de pruebas registra resultados históricos. El anexo de fuentes indica las celdas y el hash del archivo. Los dos `REPORTE_CAOS_Y_UX_QA.md` son copias con el mismo hash. [Cotejo del libro](evidencias/00-libro-cotejo.json).

## 3. Reconstrucción de alcance

| Capa | Elementos | Estado de alcance / evidencia |
|---|---|---|
| R1 seleccionado | AUTH-01/03, PROD-02, INV-01a, CAJA-01/02, VEN-01b/01c/02a | 9 HU / 41 CA, `09_Product_Backlog.md:46–54`. Seleccionado históricamente; no verificado en conjunto. |
| Adicionales declarados | CAT-01/02; PROD-01/04/05/06; VEN-05a/05b; CAJA-05; USR-01/02/03/04; PROV-01/02/04; INV-01b/02/03 | 19 HU en `r1-pmv/CONTROL_SPRINTS.md:35–65` con puntos de entrada inventariados. No se hereda «Completada». |
| Otros adicionales candidatos | AUTH-02, USR-05, INV-04 | Servicios/rutas observados; requiere contraste por CA. |
| Extras o equivalencia incompleta | Descuento, estado de categoría, stock consolidado, resumen diario; `/admin/` como superficie técnica | EXTRA SIN REQUISITO o correspondencia por decidir. No asignar automáticamente VEN-03, REP-01, INV-05/06. |
| Backlog posterior | 65 HU sin Sprint en 09; 22 tienen declaración o punto de entrada adicional | PREVISTO/FUTURO en planificación y OBSERVADO adicional son ejes distintos. Las otras 43 no se promueven a entregadas. |
| Fuera de horizonte | CLI-01/02/03; VEN-02b/02c/03/08/09; RN-13/21 | 8 ideas sin CA detallados. No se convierten en defectos actuales. |

Prefijo `HU-` omitido solo en esta tabla para facilitar lectura. El índice conserva los IDs completos. El bloqueo de pantalla VEN-01a, los flujos de solicitud/aprobación/reposición, Yape, reportes analíticos y otras funciones posteriores deben conservar su selección real; presencia en el documento de historias no implica compromiso actual.

Dependencias principales: identidad/autorización → categorías/producto → carga inicial/lotes → disponibilidad → borrador/cobro; identidad → turno propio → cobro → constancia/historial → cierre. Stock y costo conectan inventario con ventas; cambio de empleado, categoría o producto puede afectar una operación ya abierta. Las dependencias individuales y futuras están en el JSON de planificación. El recorrido de este sublote solo comprobó **alta ADMIN → consulta ALMACENERO → rechazo VENDEDOR**, sin stock ni cobro.

## 4. Inventario técnico por módulo y roles

| Módulo | Rutas propias | Plantillas | Modelos propios | Formularios | Métodos test_* definidos | Etapas principales |
|---|---:|---:|---:|---:|---:|---|
| identity | 7 | 8 | 3 | 3 | 48 | 01, 02, 13, 15 |
| catalog | 10 | 7 | 2 | 3 | 36 | 03, 07 |
| inventory | 11 | 9 | 5 | 6 | 41 | 04–08 |
| cash | 5 | 5 | 3 | 2 | 12 | 09, 12 |
| sales | 8 | 5 | 5 | 4 | 46 | 10–12 |
| app_platform | 0 | 0 | 0 | 0 | 8 | 15 |
| templates comunes | 0 | 2 | 0 | 0 | 0 | Transversal |
| Total | 41 | 36 | 18 | 18 | 191 | No ejecutados como suite |

El CSV incluye 125 campos directos de modelo, 42 campos explícitos de formulario y 11 derivados ModelForm, 359 elementos UI, 180 llamadas de mensaje, 916 textos y 359 expresiones de salida dinámica. Son ocurrencias y pueden solaparse o repetirse; no equivalen a requisitos únicos. Los campos heredados y pantallas administrativas generadas requieren expansión posterior.

| Actor | Operación observada/declarada | Evidencia en este sublote |
|---|---|---|
| Administrador (`ADMIN`) | Catálogo, empleados, categorías, proveedores, consultas, ajustes/mermas según ruta | Login, navegación de catálogo, formulario y alta ficticia ejecutados. Otros enlaces solo inventariados. |
| Almacenero (`ALMACENERO`) | Consulta de catálogo/inventario, carga/entrada/merma | Login, menú y consulta del producto ejecutados. Alta de producto denegada por HTTP GET/POST. |
| Vendedor (`VENDEDOR`) | Turno, preparación/cobro y ventas propias | Login y menú observados. Catálogo y alta denegados; operaciones de venta NO EJECUTADAS. |
| Visitante | Ingreso sin sesión | Navegación protegida redirige al login; GET/POST de catálogo/alta comprobados por HTTP. No es un cuarto rol persistido. |

Cada ruta, método HTTP, decorador, plantilla y modelo puede localizarse en el anexo técnico. Esa tabla refleja autorización declarada en código, no seguridad certificada. `/admin/` usa un acceso separado: su inventario no acredita el bloqueo de login de la aplicación ni permisos de staff. Los tres usuarios ficticios no son staff ni superusuarios.

## 5. Entorno y datos aislados

- Windows / PowerShell; Python 3.12.10 de `r1-pmv/.venv/Scripts/python.exe`; Django 5.2.18, argon2-cffi 25.1.0 y psycopg 3.2.13 observados. No se instalaron dependencias.
- Configuración propia [audit_settings.py](soporte/audit_settings.py): ignora el `.env` del operador; fuerza `APP_ENV=test`; base exclusiva `resultados/datos/etapa00-20261105/audit.sqlite3`; clave temporal local; cookies `audit00_sessionid` / `audit00_csrftoken`; correo en memoria; hosts locales.
- Advertencia operativa comprobada por lectura: `config/settings.py:21` + `config/env.py:57` hacen que `APP_ENV=test` por sí solo apunte a `r1-pmv/r1_pmv.sqlite3` para comandos normales. El runner de tests es otra cosa. Por eso **no** se utilizó el arranque/semilla ordinario del README para esta auditoría.
- Servidor propio en `127.0.0.1:8765`, sin exposición a la red; `--insecure` solo para estáticos locales con DEBUG desactivado. Se arrancó el 05/11 y se retomó el 09/11 con la misma base, sin resembrar. **Corrección de continuidad:** al cerrar 00-A se informó que estaba detenido, pero se identificó después un proceso de esa instancia que seguía respondiendo; el 09/11 se detuvieron solo los procesos `audit00.py serve` identificados. Véase [verificación del soporte](evidencias/20261109-aislamiento-soporte.md).
- SQLite permite estas comprobaciones funcionales, pero no demuestra bloqueos por fila, carreras o transacciones concurrentes de PostgreSQL. PostgreSQL NO EJECUTADO; no se intentó usar credenciales ni la base del operador.
- Migraciones aplicadas únicamente a la nueva base, incluida `identity.0005_loginattempt`. Preparación inicial: tres cuentas `admin.audit00@example.invalid`, `almacen.audit00@example.invalid`, `vendedor.audit00@example.invalid`; categoría `AUD00 Enlatados ficticios`; cero productos.
- Estado después del navegador: un producto `AUD00 Atún ficticio`, código `AUD00-001`, precio 6.50, mínimo 10, existencias físicas/vendibles 0, `is_sellable=false`; cero lotes, turnos y ventas. Datos de frontera/lotes/vencimientos/caja se prepararán cuando corresponda, no se declaran ya sembrados.
- SHA256 de la base original antes/después: `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`, 483.328 bytes. Se leyó el archivo para hash; no se abrió como base de operación. Evidencia: [preparación](evidencias/00-preparacion.json) y [persistencia final](evidencias/00-persistencia.json).

### Abrir el sitio sin modificar datos reales

Desde la raíz de trabajo, usar exclusivamente el lanzador de auditoría:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit00.py' inspect
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit00.py' serve
```

Abrir `http://127.0.0.1:8765/`. Detener con Ctrl+C en esa terminal. No usar `manage.py migrate`, `seed_pmv`, `seed_demo` o `reset` del arranque ordinario para reproducir este sublote. La base auditada ya está preparada; `prepare` se niega a resembrarla. Para una base aún no preparada, el comando `prepare` solicita una contraseña temporal sin mostrarla y crea solo el conjunto AUD00 en la ruta forzada.

Para fijar una contraseña conocida de las **tres cuentas ficticias existentes**, con el servidor detenido, ejecutar `audit00.py set-password`: la solicita sin eco y comprueba correos/nombres del conjunto AUD00. No cambia cuentas del sistema real. No se incluyen contraseñas, claves ni cookies en evidencias. `resultados/.gitignore` excluye datos y claves locales. `inspect` permite verificar ruta, conteos y hash antes de continuar.

El alta AUD00-001 ya existe. Para reproducir el caso de alta se requiere otro código y nombre ficticio. La comprobación HTTP usa el producto original y presupone datos de negocio estables. El lanzador conserva los archivos previos y guarda cualquier salida diferente en `evidencias/repeticiones/`.

El 09/11, durante 00-B, se reforzó el soporte: `http` verifica mediante desafío HMAC que el servidor posee la clave de la configuración aislada antes de solicitar la contraseña o enviar POST, y `prepare` rechaza una base existente sin marca. La prueba válida de identidad, firmas vacía/fabricada, servidor anterior sin middleware y servidor detenido se documentan en [aislamiento del soporte](evidencias/20261109-aislamiento-soporte.md). Esta protección no certifica el equipo ni un proceso que pueda leer la clave local. La rama de base sin marca se revisó solo por código. `check` e `inspect` se repitieron con resultado equivalente; **las 25 comprobaciones HTTP no se repitieron tras el cambio**. El `inspect` sobrescribió `00-persistencia.json` con el mismo estado.

## 6. Recorrido y matriz de evidencia ejecutada

`CUMPLE (caso acotado)` solo significa que el resultado concreto coincide con el esperado indicado. No cambia el estado de una HU completa ni resuelve contradicciones de alcance. Herramientas: navegador real IAB mediante CUA, HTTP real mediante `urllib` con cookies y CSRF, lectura ORM de la base aislada. No se sustituyó evidencia visual por Django Client.

| ID / fuente precisa | Actor y acción | UI / servidor / persistencia | Esperado → observado | Estado / prioridad / siguiente acción |
|---|---|---|---|---|
| E00-ENV-01 / Protocolo §2 | Preparar base separada | `soporte/audit00.py prepare`; `00-preparacion.json` | Crear solo fixtures aislados, hash original constante → observado | CUMPLE acotado / P0 / mantener aislamiento |
| E00-ENV-02 / config/settings.py | Validar configuración/modelos | `audit00.py check`; `00-check.txt` (05/11) | `check` sin incidencias, dry-run sin migraciones pendientes → ambos resultados | CUMPLE acotado / P1 / no equivale a tests de negocio |
| E00-UI-01 / AUTH-01 CA1, CA4 (`08:18,21`) | Visitante → ingreso ADMIN | `/productos/` redirigió `/?next=/productos/`; login válido abrió catálogo | Acceso autenticado y menú ADMIN → observado | PARCIAL frente a HU / P1 / límites y credenciales inválidas en 01 |
| E00-UI-02 / PROD-02 CA1, CA2, CA4, CA5 (`08:218–222`) | ADMIN registra datos normales | Menú Registrar producto → POST `/productos/nuevo/` → confirmación; `catalog/views.py:96`, servicio `register_canned_product`; producto persistido | 6.50, mínimo inicial 10, stock 0/no vendible → observado | CUMPLE caso normal; HU PARCIAL / P1 / categoría es ampliación pendiente DOC-00-04; fronteras en 03 |
| E00-UI-03 / PROD-01 (`08:204–209`) y guía21:12 | ALMACENERO consulta producto recién creado | Menú Catálogo de productos, tabla y ORM; `20261109-04-almacen-catalogo.*` | Mismo código/nombre/precio/mínimo; sin stock vigente → observado | CUMPLE comunicación de ese dato entre roles / P1 / no valida lista completa ni alertas |
| E00-UI-04 / RN-29 (`07:347`), guía21:13 | VENDEDOR solicita catálogo directo | Pantalla «No tienes permiso para esta operación»; HTTP 403 | Denegación según código/guía → observada | CONFLICTO DE FUENTES con actor de PROD-01; DOC-00-14 / P1 / decidir en 03 |
| E00-HTTP-01 / PROD-02 CA5 (`08:222`) | ALMACENERO/VENDEDOR/visitante intentan alta | GET y POST válido con CSRF; `20261109-08-http.json`; snapshot de producto/lotes/turnos/ventas | Roles autenticados 403; anónimo 302 al ingreso; ningún producto extra → observado | CUMPLE casos enviados / P1 / otras rutas y métodos quedan pendientes |
| E00-UI-05 / AUTH-03 (`08:41–43`) | Tres roles cierran sesión | Enlace → confirmación → POST → ingreso; sin borradores/turnos | Salida al ingreso → observada; HTTP logout 302 | PARCIAL frente a HU / P1 / sesiones concurrentes y revocación en 02 |
| E00-HTTP-02 / Protocolo §2 | Cotejar integridad después del rechazo | Snapshot producto idéntico; 0 lotes/turnos/ventas; hash original igual | Sin mutación de esos datos de negocio → observado | CUMPLE acotado / P0 / no confundir cambios legítimos de sesión/last_login con negocio |

Las referencias `08`, `07` y `guía21` en esta tabla remiten a sus archivos raíz completos, identificados en §2. No se verificó aún si todas las variantes de persistencia o auditoría interna permanecen invariantes.

**Resultado nuevo:** 25/25 comprobaciones del script HTTP/persistencia el 09/11/2026 a las 09:58 Lima; desglose exacto esperado/observado en [JSON de ejecución](evidencias/20261109-08-http.json). Incluyen estados HTTP, redirecciones, dos verificaciones de presencia y dos comparaciones de persistencia/hash. No son 25 HU, 25 CA completos ni una suite de 191/202 pruebas. La suite del proyecto quedó **NO EJECUTADA** en esta etapa.

Capturas revisadas: [alta confirmada](evidencias/20261109-02-producto-creado.jpg), [consulta del almacenero](evidencias/20261109-04-almacen-catalogo.jpg), [denegación del vendedor](evidencias/20261109-06-vendedor-denegado.jpg). Los TXT adyacentes de confirmación, consulta, menú y denegación preservan árboles accesibles sanitizados. El TXT `20261109-01-admin-form.txt` solo contiene un aviso de árbol sin cambios, no el formulario completo; la descripción de campos de §6 procede de la observación de navegador y del código, y su captura persistente queda pendiente. El catálogo usa desplazamiento horizontal en el ancho del panel; la captura no muestra todas sus columnas a la vez, y el árbol accesible documenta el resto. No se declaró revisión responsive completa.

### Campos, acciones, mensajes y salidas del recorrido acotado

| Elemento / propósito | Definición localizada / valor observado | Validación y persistencia examinadas |
|---|---|---|
| Correo de trabajo / identidad | `identity/forms.py:6`; EmailField obligatorio, autocomplete username; normalización `identity/models.py:80` | Solo correos ficticios válidos de los tres roles. Límites efectivos/vacío/inválido/mayúsculas NO EJECUTADOS. |
| Contraseña / autenticación | `identity/forms.py:16`; PasswordInput obligatorio, `strip=False`; valor oculto | Solo contraseña correcta, sin incluirla en evidencias. Longitud/límites/error/bloqueo NO EJECUTADOS. |
| Nombre del producto | `catalog/forms.py:28`, `catalog/models.py:50`; requerido, máximo 160; normaliza espacios en formulario | «AUD00 Atún ficticio» persistido. Repetición, vacíos, formato y fronteras pendientes. |
| Código de barras | Formulario/servicio/modelo; máximo 64, normalización NFKC/sin espacios/casefold; unicidad declarada | AUD00-001 persistido; duplicados, normalización y manipulación NO EJECUTADOS. |
| Categoría | Selector de categorías activas, obligatorio; inicialmente sin selección | AUD00 Enlatados ficticios persistida; caso ampliado respecto a categoría sembrada histórica. Decisión DOC-00-04. |
| Unidad | UND preseleccionada; modelo restringe UND y vencimiento obligatorio | Se conservó UND. Alteración de petición NO EJECUTADA. |
| Precio final con IGV (S/) | Requerido, mínimo 0.01, 2 decimales; formulario máximo 9999999.99 | 6.50 guardado/mostrado 6,50. Redondeo, límites, formato inválido y cálculo tributario NO EJECUTADOS. |
| Existencia mínima | Inicial 10; opcional; vacío→10; entero 0..999999 en formulario | Se mantuvo 10 (no se vació). No atribuir prueba al default por vacío. |
| Registrar / confirmar / volver / cancelar | Botón de alta, enlaces de retorno y confirmación de logout | Alta y logout usados; cancelar/atrás/reenvío/recarga del alta NO EJECUTADOS. |
| Confirmación | «El producto se creó con cero existencias», precio, mínimo, stock físico y disponibilidad | UI y ORM consistentes en el único producto creado. |
| Catálogo y búsqueda | Nombre, categoría, código, precio, mínimo y «Sin stock vigente»; campo de búsqueda y botón | Consulta sin filtro ejecutada. Filtro, existencias numéricas, alertas y otros estados pendientes. |
| Denegación | `identity/authorization.py:27` y plantilla 403; mensaje visible de falta de permiso | GET vendedor y HTTP GET/POST de alta denegados. Mensajes de errores de campos pendientes. |

Esta tabla no sustituye el inventario del resto de campos/salidas del CSV ni su futura ficha completa de fronteras y errores.

## 7. Hallazgos, cambios y propuestas

Los 13 conflictos documentales anteriores están detallados con alternativas en [anexo de conflictos](anexos/ETAPA-00-conflictos-planificacion.md). Prioridades principales: RN-29/constancia ADMIN; solicitud aprobada frente a entrada directa; categoría única frente a categorías activas; bloqueo 5/15 minutos; IDs de descuento/movimientos mal reutilizados; filtros históricos incompletos; panel confundido con reportes; cifras de pruebas históricas; grupos QA con ordinales ambiguos.

| ID nuevo | Evidencia / clasificación | Decisión o siguiente acción |
|---|---|---|
| DOC-00-14 / P1 | `08_Historias_de_Usuario.md:204` dice administrador o vendedor para catálogo; `21_Alcance_Actual_y_Diferencias.md:11–13` describe catálogo para ADMIN/ALMACENERO; `catalog/views.py:77` y navegador/HTTP niegan VENDEDOR. CONFLICTO DE FUENTES, confirmado el comportamiento. | Etapa 03: alternativa A, catálogo operativo para almacén y consulta vendedor solo en venta; alternativa B, habilitar catálogo vendedor con campos acordados. No ampliar permisos ni reescribir HU sin resolver alcance. |
| OBS-00-15 / P2 | PROD-01 CA1 (`08:207`) pide existencias disponibles; tabla observada muestra mínimo/disponibilidad textual, sin columna numérica de existencias. Candidato PARCIAL frente a HU adicional. | Auditar con producto con lotes en 03/07, filtros y alertas CA2/3. No cerrar fallo global con el único producto sin stock. |
| ENV-00-16 / P0 operativo | Arranque ordinario con APP_ENV=test reutiliza SQLite local para comandos normales. Aislamiento requerido por protocolo. | Resuelto para esta auditoría con configuración externa forzada y hash antes/después. No se cambió configuración de producción. |
| INVERSA-00-01 / P1 | RN-06 (`07:108`) establece alerta con existencias vendibles iguales o inferiores al mínimo para las HU indicadas. `identity/views.py:203–206` e `inventory/views.py:353–356` usan menor que o cero; ramas de plantilla usan menor que. Discrepancia estática candidata, NO EJECUTADA. | Etapas 07/13: producto y categoría activos, mínimo 10, lotes vigentes 9/10/11 y mínimo 0; contrastar indicadores y alcance de cada extra. |
| INVERSA-00-02 / P1 | Panel excluye categorías inactivas del conteo de stock bajo y la lista de inventario no usa el mismo filtro. | NO EJECUTADO. Etapas 03/07/13: comprobar poblaciones y decidir si deben coincidir o explicarse. |
| INVERSA-00-03 / P2 | Panel usa 30 días (`identity/views.py:208–210`); DASH-03 menciona 7 días (`08:721`). | PARCIAL candidato; aclarar si son señales distintas o sustitución y comprobar fronteras en 07/13. |
| INVERSA-00-04 / P1 | Servicio de categoría invierte el estado por POST (`catalog/services.py:25–31`). | Riesgo por reintento NO EJECUTADO; decidir alternar o establecer estado explícito y probar dobles envíos en 03. |

Cambios de esta ejecución: nuevos informes, inventarios, matriz, evidencia y lanzador de auditoría; corrección documental inequívoca de `auditoria_por_etapas/LEEME.md` que decía que los resultados todavía no existían; verificación de identidad y protección de preparación en el soporte aislado. **No se modificó código funcional de `r1-pmv`, el XLSX ni documentos históricos de requisitos.** No se detectó un defecto funcional inequívoco dentro del único caso normal que justificase cambiar la aplicación; los conflictos de permisos/alcance permanecen explícitos.

Propuestas, no aceptadas por este informe: `PROP-E00-HU-01` descuento con criterios de límites/permisos/persistencia; `PROP-E00-HU-02` estado de categoría y efecto entre operaciones; tareas técnicas `PROP-E00-T-01..03` y pruebas `PROP-E00-PR-01/02`, detalladas en el anexo. `PROP-E00-T-03` cuenta con estructura inicial de cobertura; falta conciliación semántica completa. `PROP-E00-T-04` descompuso las nueve filas QA en 30 afirmaciones identificables, sin modificar CA base. Los nuevos mapas proponen `PROP-E00-HU-03/04` para resumen y stock, `PROP-E00-T-05/06` y `PROP-E00-PR-03/04`, con alternativas de ampliar HU existentes; selección y criterios siguen propuestos y NO EJECUTADOS.

## 8. Pendientes, datos futuros y cursor exacto

Persisten NO EJECUTADOS: límites/inválidos/duplicados de campos, bloqueo/inactividad, sesiones simultáneas, cambios de personal, categorías/proveedores, lotes y FEFO, entradas/mermas/ajustes, caja, borradores/cobro/descuento, impuestos/constancias, reportes, PostgreSQL, admin, despliegue y normativa. Ningún enlace visible prueba su operación. Las 25 comprobaciones de este sublote no autorizan rebajar estos estados.

Conjunto ficticio futuro propuesto (NO CREADO): AUD01 cuentas inactiva/segundo vendedor para 01/02; AUD05 productos sin carga y lotes futuro/hoy/vencido para 05/07 (fechas relativas a Lima); AUD09 caja/turnos propios y ajenos para 09; AUD11 precios/cantidades de frontera y venta previa para 11/12. Cada etapa debe crear solo sus fixtures mediante la configuración aislada y comprobar efectos entre roles; no ejecutar semillas destructivas generales.

**Siguiente cursor global: ETAPA-01 / HU-AUTH-01 / CA-01, `08_Historias_de_Usuario.md:18`.** Abrir `auditoria_por_etapas/01_Ingreso_y_bloqueo.md`, leer el protocolo y el estado general y retomar `LoginForm` en GET/POST `/`. Las salidas generadas de `login.html:23–27` están inventariadas en [formularios generados](anexos/ETAPA-00-formularios-generados.md). El primer caso requiere cuenta activa de cada rol, ingreso correcto, sesión persistida y destino autorizado. Después continuar por CA-02, CA-03, CA-04 y HU-AUTH-02 conforme al prompt 01.

Las discrepancias y propuestas permanecen identificadas con estado y etapa de resolución. El inventario 00 queda cerrado con esas remisiones. Cada criterio de producto conservará su resultado parcial, pendiente o futuro hasta que se ejecute su propia auditoría.

Para retomar en otro chat, leer este informe y ESTADO_GENERAL, comprobar cambios de fuentes, ejecutar `inspect` y usar `serve` para la instancia aislada. El comando `set-password` permite configurar las credenciales ficticias si hace falta. La [cola 00–17](ESTADO_GENERAL.md) conserva la cobertura y el primer caso de cada etapa.


## 9. Conciliación y cierre de la etapa 00

El cierre se refiere al trabajo específico del prompt 00. Las condiciones observadas, los conflictos de fuentes y las alternativas están documentados y asignados a una etapa de comprobación. La aceptación funcional del producto conserva sus estados individuales en la matriz.

| Entregable de 00 | Resultado de cierre | Evidencia |
|---|---|---|
| Reconstrucción R1, ampliaciones y futuro | Inventario terminado, con 9 HU R1, 65 posteriores y 8 ideas fuera de horizonte | Índice de planificación y conflictos |
| HU/CA/RN/tareas y dependencias | 219 CA base, 30 reglas y 67 tareas identificados. Nueve grupos QA descompuestos en 30 afirmaciones | JSON de planificación y anexo QA |
| Rutas, pantallas, roles y modelos | 106 patrones, 36 plantillas propias y 18 modelos propios. Censo administrativo y técnico añadido | Código, superficie UI y admin |
| Campos, acciones, mensajes y salidas | 53 campos efectivos, cuatro de gestión de lotes y 2.367 localizaciones UI/servidor con destino de revisión | Formularios y superficie UI |
| Fuentes y versión | Repositorio, cambios previos, históricos y libro cotejados con límites documentados | Fuentes, cotejo del libro y verificación final |
| Entorno ficticio | Tres cuentas, categoría y producto de auditoría. Base aislada y hash de original comprobados | Preparación, persistencia y soporte |
| Planificación y ejecución observada | Ocho CA enlazados a muestra parcial de 00-A. Los otros 211 CA conservan NO EJECUTADO | Matriz de cobertura y evidencia HTTP/UI |
| Cola y continuidad | Etapas 01–17 con ámbito, dependencia y cursor. Próximo caso AUTH-01/CA-01 | ESTADO_GENERAL y prompt 01 |

El 09/11 se repitieron `check`, comprobación de migraciones y lectura de persistencia del entorno aislado sin incidencias. Los extractores de formularios y admin bloquearon SQL durante la introspección. Se verificaron coordenadas y cardinalidades de los índices. Las 25 comprobaciones de HTTP/persistencia de 00-A y las capturas fechadas conservan su procedencia. La suite completa del proyecto figura NO EJECUTADA en esta etapa.

Se corrigieron el cursor histórico de USR-01/03, las referencias a reposición (familia SOL) y la matriz que aún indicaba ausencia de evidencia para criterios parcialmente observados. También se completaron los enlaces candidatos de DASH-01/03 y REP-05/06 hacia panel y stock, conservando la decisión de alcance pendiente. El lanzador ahora preserva evidencia previa al repetir una salida diferente. Estas correcciones pertenecen a los artefactos y herramientas de auditoría.

La captura persistente incompleta del formulario de alta de 00-A queda registrada en §6. El inventario de 00-C identifica sus campos con fuentes y metadatos. La etapa 03 tendrá que capturar sus estados al ejecutar el formulario. Los campos heredados y pantallas administrativas se inventariaron con metadatos y familias de operación. Su acceso real, combinaciones y efectos tienen el caso SEC-15-01 asignado.

La evidencia reproducible del cierre está en [verificación final de inventario](evidencias/00-cierre-verificacion-final.json): 55 comprobaciones estructurales y de conservación conformes. Incluyen enlaces, coordenadas, cardinalidades, hashes, cambios Git previos, ausencia de procesos del servidor de auditoría y conservación de evidencia al repetir una salida. Son controles del inventario y su soporte; no nuevas pruebas de historias de negocio. El primer corte de esta verificación se conserva en `evidencias/00-cierre-verificacion.json`.

Para repetir estos controles desde la raíz, ejecutar `& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/verificar_cierre_00.py'`. El [script](soporte/verificar_cierre_00.py) conserva el corte anterior y escribe nuevas ejecuciones en `evidencias/repeticiones/`. Los pendientes funcionales y las propuestas conservan su severidad y estado en los anexos. La fecha de cierre corresponde al alcance de esta etapa.
