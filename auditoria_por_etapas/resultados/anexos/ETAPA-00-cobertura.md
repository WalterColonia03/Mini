# ETAPA 00 — Matriz inicial de cobertura y cola

Construcción: **9 de noviembre de 2026**, America/Lima. Fuente del índice de planificación: extracción del 5 de noviembre. Este anexo no ejecuta la aplicación ni sus pruebas; distribuye identificadores y localizaciones para las etapas. Los casos de arranque y navegador de esta sesión se registran separadamente en `../ETAPA-00.md` y `../evidencias/` y no transforman automáticamente los CA de esta matriz en aprobados.

## Archivos y cardinalidades

- `ETAPA-00-cobertura.csv`: **236 registros de tres clases diferentes**: 219 CA base de 74 HU; 8 ideas fuera del horizonte sin CA; 9 grupos históricos QA de `08_Historias_de_Usuario.md:869–877`. No sumar estas tres clases como si fueran 236 CA.
- Hay **41 CA de las 9 HU R1 seleccionadas** y **178 CA de las 65 HU posteriores**. Ocho filas tienen enlaces a observaciones acotadas del recorrido 00-A y estado PARCIAL. Los otros 211 criterios conservan NO EJECUTADO en esta auditoría. La matriz mantiene el alcance observado y el caso pendiente al nivel de cada criterio.
- `ETAPA-00-cobertura-inversa.csv`: **106 patrones resueltos**, 41 rutas de negocio y 65 patrones bajo `/admin/`, tomados de `../evidencias/00-rutas-resueltas.json`. Los patrones de Django Admin incluyen resoluciones técnicas y un catch-all; no representan 65 pantallas independientes.
- `ETAPA-00-cobertura-conteos.json`: conteos comprobados por módulo y etapa primaria.
- `construir_cobertura_00.py`: generador reproducible; únicamente lee JSON/CSV y líneas de Markdown locales. No importa Django ni accede a la base.

Las fuentes individuales de cada CA apuntan a la línea correspondiente de 08, además de la HU y fila de backlog. Los CA R1 conservan referencias de pruebas **planificadas históricas** desde 03, con su origen, sin tratarlas como pruebas ejecutadas hoy. Los grupos QA tienen localizadores `QA-HIST-08-L869`…`QA-HIST-08-L877`: son identificadores de fila para auditoría, no nuevos IDs de CA aceptados.

## Cómo leer los vínculos

Una **ruta candidata** localiza el flujo que debe revisarse; no demuestra que cubra un criterio. Modelos y archivos de pruebas son candidatos por módulo: no se afirma una correspondencia exacta CA–método `test_*`. Las HU sin ruta asignada permanecen con ese dato explícito; ausencia de asignación en este mapa no demuestra ausencia absoluta de implementación.

Cada registro incluye actor de la planificación, roles estáticos de rutas candidatas cuando existen, selección documental, declaración histórica adicional, reglas, dependencias, fuente, requisito literal, esperado, observado, evidencia, estados, prioridad de revisión y siguiente acción. `P1/P2` en esta matriz prioriza la **revisión**, no es una clasificación automática de severidad de un defecto. Los conflictos concretos y su severidad constan en el informe y en `ETAPA-00-conflictos-planificacion.md`.

El mapa inverso incluye todas las rutas del resolver y distingue las rutas con HU candidatas de las superficies que requieren requisito propio. En particular, `category-toggle` se vincula al agregado QA de 08:876 pero no se fuerza a CAT-03 (editar nombre) ni CAT-04 (eliminar); `stock-overview` conserva la necesidad de delimitar stock, alertas y reportes. `/admin/` queda como superficie técnica de alcance y permisos por decidir en etapa 15.

Para acciones, mensajes, campos y salidas dentro de cada pantalla se usa el índice granular `ETAPA-00-inventario-codigo.csv`; este mapa por CA no sustituye ese inventario ni una revisión semántica elemento por elemento. Un enlace visible, una cadena de error o un método de prueba encontrado no constituye un caso probado.

## Índice por módulo de planificación

| Módulo | CA base | Etapas primarias asignadas | Localización candidata |
|---|---:|---|---|
| AUTH | 20 | 01, 02 | identity; ingreso/salida; recuperación futura por localizar |
| USR | 17 | 02 | identity; empleados |
| LOG | 3 | 13 | identidad/accesos futuros; revisar seguridad transversal en 15 |
| CAT | 9 | 03 | catalog; categorías |
| PROD | 21 | 03, 07 | catalog; altas/listado/edición/estado/vencimientos |
| PROV | 10 | 04 | inventory; proveedores |
| INV | 22 | 05, 06, 08 | inventory; carga/entrada/mermas/ajustes/movimientos |
| SOL | 18 | 06 | reposiciones futuras; distinguir entrada directa actual |
| CAJA | 21 | 09 | cash; apertura/cierre/historial; autorizaciones futuras |
| VEN | 39 | 10, 11, 12 | sales; borrador/cobro/constancia/historial y futuro |
| CONF | 5 | 13 | configuración futura por localizar |
| DASH | 13 | 13 | identity dashboard como candidato parcial, no HU completa |
| REP | 21 | 13 | consultas/reportes futuros; resumen diario no equivale a reporte analítico |
| **Total** | **219** | | |

## Cola de etapas y dependencia principal

La asignación primaria evita contar dos veces un CA; no impide revisiones transversales posteriores. Las etapas 14–17 no generan CA nuevos por sí mismas.

| Etapa | CA base asignados | Orden de trabajo / dependencia |
|---|---:|---|
| 01 | 12 | Ingreso y bloqueo; base para permisos de todo el sistema. Iniciar HU-AUTH-01/CA-01 (`08_Historias_de_Usuario.md:18`). |
| 02 | 25 | Sesión y empleados; relación con borrador y turno. |
| 03 | 27 | Categorías y producto; conciliar actor de catálogo y categoría fija vs cualquier activa. |
| 04 | 10 | Proveedor; dependencia para entradas/lotes. |
| 05 | 5 | Carga inicial; producto y almacenero. |
| 06 | 20 | Entrada posterior y reposición; resolver excepción frente a solicitud aprobada. |
| 07 | 3 | CA de vencimientos de PROD-06; además stock/alertas/elementos sin CA atómico asignado. |
| 08 | 15 | Mermas, ajustes, movimientos; conservar trazabilidad y costo. |
| 09 | 21 | Apertura/cierre; turnos, caja e historial. |
| 10 | 10 | Borrador/búsqueda y bloqueo de pantalla futuro; depende de stock y turno. |
| 11 | 20 | Cobro y anulaciones/pago digital futuros; descuento requiere HU/regla propia. |
| 12 | 9 | Constancias e historial; además cruces con historial de caja e ideas sin CA. |
| 13 | 42 | Panel/reportes/configuración/log futuros; distinguir resumen observado de producto deseado. |
| 14 | — | Integración de los CA previos entre roles; no auditada por terminar inventario. |
| 15 | — | Seguridad, `/admin/`, PostgreSQL/concurrencia, despliegue; no acreditados por SQLite. |
| 16 | — | Afirmaciones normativas/comerciales, datos y salidas; no certificadas por el código. |
| 17 | — | Conciliar cobertura, decisiones y evidencia; no cerrar mientras haya pendientes. |

Los nueve grupos QA se asignan primariamente a 01, 02, 03, 05, 08 (dos grupos), 09, 11 y 12. Cada fila de la matriz remite a las afirmaciones de su grupo en [el desglose histórico](ETAPA-00-agregados-QA.md). Las ocho ideas fuera del horizonte conservan una fila propia.

## Conflicto adicional del catálogo: pendiente de etapa 03

**E00-COV-01 — CONFLICTO DE FUENTES, P1 de revisión de permisos.** `08_Historias_de_Usuario.md:204` define HU-PROD-01 para administrador **o vendedor**; `r1-pmv/catalog/views.py:77–79` permite ADMIN/ALMACENERO y guía `21_Alcance_Actual_y_Diferencias.md:12–13` describe esa distribución. El padre registró vendedor denegado en `../evidencias/20261109-06-vendedor-denegado.txt`. Esa denegación concuerda con el código, pero no resuelve el actor de la HU; no se debe llamarla aprobación integral de PROD-01.

Opciones pendientes: (a) incorporar un catálogo de consulta al vendedor con campos y límites acordados; (b) mantener consulta de productos del vendedor dentro de preparación de venta y revisar la HU vigente con una decisión trazable; (c) conservar HU futura y documentar que el catálogo actual corresponde a una ampliación distinta. No cambiar permisos sin determinar qué alternativa representa el alcance.

`08_Historias_de_Usuario.md:207` pide existencias disponibles y `:209` señal de alerta por mínimo. El catálogo visto por el padre (`../evidencias/20261109-04-almacen-catalogo.txt`) enumera stock mínimo y disponibilidad textual, y se observó el caso sin stock; no se verificaron stock positivo ni alerta de frontera. La revisión debe comprobar si existe salida numérica, qué rol la recibe y si la alerta pertenece a esa pantalla. No sustituir el CA por una pantalla de inventario distinta ni aprobarlo por mostrar “Sin stock vigente”.

## Reproducción y cursor

Desde la raíz del proyecto:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/anexos/construir_cobertura_00.py'
```

El generador comprueba 219 CA base, 41 R1, 8 ideas, 9 grupos históricos, 236 IDs únicos y 106 patrones (65 `/admin/`). Estos controles validan la estructura del índice, **no requisitos del minimarket**. En esta tarea no se ejecutó ningún test funcional.

Cursor funcional al cierre de la matriz: etapa 01, HU-AUTH-01/CA-01 (`08_Historias_de_Usuario.md:18`). Retomar el inventario de LoginForm de 00-C y contrastar los campos y las salidas con navegador, servidor, efectos de sesión y roles. Conservar E00-COV-01 para etapa 03. [Estado general](../ESTADO_GENERAL.md).
