# Etapa 03-J · Confirmación del estado de categorías

**10/11/2026, America/Lima.** El usuario aceptó explicar el impacto y pedir confirmación al activar o desactivar una categoría. También eligió rechazar una pantalla antigua si otro administrador había cambiado su estado. La acción existía bajo el agregado QA de `08_Historias_de_Usuario.md`, fila 876. Este corte vincula ambas decisiones con `PROP-E00-HU-02` y la parte correspondiente de `PROP-E03-T01`. El criterio de eliminación de CAT04 conserva su alcance futuro.

## Alcance, fuentes y matriz

Se aplicó el protocolo común y se retomó el cursor del corte I. Antes de editar se identificaron actor ADMIN, controles, rutas, reglas de impacto y efectos por rol. Fuentes específicas: 08, líneas 166–197 y 876, matriz 03 para BUG-028/033, `QA-FIX-CAT-01` en 16, RN-29 y los cortes 03-A/E. La selección histórica de 01/09/14 y CONTROL_SPRINTS se conserva. El XLSX se protegió por hash. [Inventario previo](../evidencias/03-J-inventario-20261110T171113912354Z.json).

| ID, prioridad y entrada | Comportamiento esperado y observado | Verificación |
|---|---|---|
| J-CA1 · P1 · ADMIN, lista → Activar/Desactivar | Se abre una revisión de solo lectura con nombre, estado, acción y consecuencias. Productos asociados, ventas en preparación y existencias físicas son cifras informativas del momento. Cancelar vuelve a la lista. Recargar conserva el estado. | CUMPLE muestra. J01–03, J19, J23–25. |
| J-CA2 · P1 · ADMIN confirma | Al desactivar, el almacenero observa la categoría suspendida, conserva sus 19 unidades vigentes y los productos salen de los selectores de entrada/carga. El vendedor pierde la oferta del producto. Actualizar y cobrar su línea se rechazan. La categoría y su versión son los únicos campos comerciales modificados en las instantáneas. | CUMPLE muestra. J04, J07–12. |
| J-CA2 · reactivación | Se recuperan oferta y selección cuando el producto cumple las condiciones. Un producto deshabilitado individualmente sigue inactivo. Se conservan cantidades, referencias, borradores, turno y datos de la constancia. | CUMPLE muestra. J19/20/26. |
| J-CA3 · P1 · dos administradores | Lista o confirmación obsoleta devuelve 409, muestra el estado actual y ofrece «Revisar categorías». Un doble envío conserva el destino. La versión permite detectar que la categoría cambió dos veces y volvió al mismo estado. | CUMPLE muestra. J05/06/21/22, J-R1–R3 en ambos motores. |
| J-CA4 · P1 · acceso por rol | ADMIN revisa/confirma. ALMACENERO y VENDEDOR reciben 403 en revisión y aplicación. Visitante se redirige al ingreso. Métodos incorrectos, UUID ausente, solicitud sin CSRF y campos inválidos conservan las filas. | CUMPLE muestra. J13–18 y pruebas Django. |

La matriz inversa queda así: `GET /productos/categorias/` ofrece el botón contextual y transmite destino/versión a `GET /productos/categorias/<uuid>/estado/confirmar/`. La confirmación ofrece «Confirmar activación» o «Confirmar desactivación» y «Cancelar». Solo `POST /productos/categorias/<uuid>/estado/` aplica el cambio. El éxito redirige y anuncia «Categoría «…» ahora está activa/inactiva.». Los errores se muestran en la propia pantalla con la acción «Revisar categorías». La reproducción incluyó Chrome de escritorio, ventana de 390 × 844 y abrir/cancelar con JavaScript deshabilitado.

| Campo o salida | Contrato comprobado |
|---|---|
| UUID y estado actual | La fila identifica la categoría. En el recorrido, activa al comenzar. UUID válido inexistente devuelve 404. |
| `is_active`, `state_version`, `confirm` | Destino oculto `true`/`false`. Versión entera decimal ASCII no negativa, hasta 9223372036854775807, inicial 0. El POST requiere `confirm=yes`, versión y destino. Ausencia o formato inválido devuelve 400. Confirmación antigua devuelve 409. La versión aumenta una vez por cambio efectivo. Los clientes HTTP antiguos necesitan abrir de nuevo la lista. |
| Productos asociados | Conteo de todas las fichas de la categoría, incluidas inactivas. La muestra mostró 3. |
| Ventas en preparación | Conteo de borradores ACTIVE distintos con al menos una línea de la categoría. La muestra mostró 1. |
| Existencias físicas registradas (UND) | Suma de cantidades disponibles en lotes de la categoría. La muestra mostró 23, de las que 19 estaban vigentes y 4 vencidas. El recuento visible no reserva unidades ni el importe de un cobro. |

## Ejecución y correcciones

El modelo añade `Category.state_version`. La migración `catalog.0006_category_state_version` asigna cero a categorías existentes. En el servicio, un UPDATE compara versión y estado y aumenta la versión en la misma escritura. El POST comercial exige la versión revisada. El servicio interno mantiene el modo de alternar estado para sus llamadas preexistentes. Productos y categorías conservan acciones distintas. Las adendas de 08, 09, 16, 03 y 21 registran la decisión, los criterios y las pruebas.

| Ejecución | Resultado |
|---|---|
| Preparación de pruebas | En el primer intento, se descubrieron 98 métodos y se ejecutaron 91. El alta de datos ficticios de los 7 nuevos usaba un código de caja distinto del requerido. Se corrigió a `CAJA-01`. [Registro inicial](../evidencias/03-J-tests-20261110T171321742969Z/tests.txt). |
| Regresión final | **98/98** métodos de catálogo. Incluye revisión/cancelación, conservación, reenvío, ciclo de estados, formato de versión, roles y validación del servicio. `check` y `makemigrations --check --dry-run` superados. [Log](../evidencias/03-J-tests-20261110T172054000837Z/tests.txt). |
| Chrome y servidor | **32/32** comprobaciones en la repetición final. Dos cuentas ADMIN distintas, una ALMACENERO, una VENDEDOR y visitante. Las imágenes muestran la revisión, el aviso al segundo administrador y el control en vista móvil. [Resultados](../evidencias/03-J-browser-20261110T172105045406Z/browser.json) · [Revisión](../evidencias/03-J-browser-20261110T172105045406Z/02-impacto.png) · [Conflicto](../evidencias/03-J-browser-20261110T172105045406Z/06-conflicto.png) · [Vista móvil](../evidencias/03-J-browser-20261110T172105045406Z/23-movil.png). |
| SQLite concurrente | El primer servicio leía antes de guardar y se observó `database is locked` con error interno. Ese intento terminó sin JSON final. Tras condicionar la escritura, **3/3** escenarios con dos conexiones devolvieron exactamente un 302 y un 409. [Nota del fallo observado](../evidencias/03-J-sqlite-race-20261110T171905215655Z/nota-del-intento.md) · [Repetición final](../evidencias/03-J-sqlite-race-20261110T172006895618Z/result.json). |
| PostgreSQL | **4/4**. En migración 0005→0006 una categoría inactiva inició versión 0 conservando su fila y el producto relacionado. Dos administradores se sincronizaron en la escritura para las mismas tres carreras. Un 302 y un 409 en cada caso. [Clúster aislado y resultados](../evidencias/03-J-postgresql-20261110T172019957099Z.json). |

Las carreras comprenden dos intentos de suspensión con versión 0, activación vigente frente a una suspensión antigua y suspensión vigente frente a una activación antigua. Los estados finales fueron inactiva/1, activa/2 e inactiva/3. Para intenciones opuestas se usan versiones distintas que realmente pueden obtener dos pantallas comerciales.

## Datos y reproducción

Base final de navegador `datos/etapa03j-20261110T172105045406Z/audit.sqlite3`. Una categoría activa, versión 2, tres productos, dos cargas, dos lotes, una venta confirmada, un borrador activo de dos unidades y turno OPEN de S/ 50. Las capturas ORM inicial/final coinciden en todos los grupos registrados salvo la versión de la categoría. Los lotes, ventas y borradores eran ficticios. Se conservaron base original, bases anteriores y libro por hash. Se verificó el cierre de los puertos HTTP y PostgreSQL de los recorridos finales. [Inicial](../evidencias/03-J-browser-20261110T172105045406Z/orm-initial.json) · [Final](../evidencias/03-J-browser-20261110T172105045406Z/orm-final.json) · [Cierre](../evidencias/03-J-cierre.json).

Desde la raíz del proyecto, ejecutar en orden. Cada ejecución funcional prepara datos aislados nuevos. El último comando coteja la evidencia fechada de este informe.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03j_run.py' tests catalog
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03j_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03j_run.py' sqlite-race
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03j_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/cierre_etapa03j.py'
```

## Cobertura y continuidad

Los **27 CA base** conservan **21 CUMPLE en la muestra y 6 PREVISTO/FUTURO**. Los cuatro criterios suplementarios J-CA1 a J-CA4 cumplen en los casos descritos. El inventario aumenta en una ruta y una plantilla de catálogo. La protección por versión cubre la acción comercial de cambio de estado. Cambios directos de estado por SQL, siembra o administración técnica no pasan necesariamente por este servicio y precisan revisión antes de combinar esas vías en explotación. Los conteos de impacto son informativos. La simultaneidad con un cobro o una entrada de mercadería sigue asignada a la etapa 15. Suite global, lector físico y accesibilidad con lector de pantalla quedan NO EJECUTADOS en este corte.

**Cursor 03-K / HU-PROD-03 CA01 / PROP-03G-SCAN-T01.** Con la categoría de prueba activa, abrir «Registrar producto» como ADMIN, enfocar «Código de barras» y verificar en entorno aislado la lectura real teléfono → Barcode to PC Server → navegador, incluidos ceros iniciales y ausencia de guardado automático. Registrar dispositivo, versiones y perfil. Si falta el equipo, conservar NO EJECUTADO y continuar con `PROP-03E-CA01` en HU-PROD-05 CA02 (precondiciones de reactivación). El aviso inmediato de duplicado en CA02 del lector sigue pendiente de incorporación. Las migraciones 0003 a 0006 quedan pendientes de despliegue en la base de uso.
