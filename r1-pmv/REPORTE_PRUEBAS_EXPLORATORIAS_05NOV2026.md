# REPORTE DE PRUEBAS EXPLORATORIAS — R1-PMV (05/11/2026)

> Informe histórico filtrado al alcance del minimarket; los totales originales incluyen casos retirados y no deben interpretarse como métricas actuales.

## 0. Entorno

| Parámetro | Detalle |
|---|---|
| **Commit de partida** | `7816d33` (`fix: align inventory and logout acceptance criteria`) |
| **Variables de entorno** | `APP_ENV=local`, `DATABASE_URL=sqlite`, `DJANGO_SECRET_KEY=local-test-key-prompt` |
| **Migraciones pendientes al iniciar** | Ninguna (`No migrations to apply` — las 3 migraciones faltantes detectadas en `AUDITORIA_USABILIDAD_05NOV2026.md` §3 ya estaban aplicadas en `r1_pmv.sqlite3`). |
| **Datos semilla (`seed_demo`)** | Ejecutado de forma idempotente (`Productos demo creados: 0`; ya existían 5 productos activos, 6 lotes, 1 turno abierto `CAJA-01` con S/ 200.00, 1 turno cerrado, 1 venta previa `V-00000001` por S/ 10.00 con descuento S/ 3.00, y cuentas del minimarket). |
| **Respaldo previo y restauración** | Respaldo creado en `r1_pmv.backup_20261105_0212.sqlite3` antes de ejecutar las pruebas y restaurado íntegramente al finalizar. |
| **Herramientas utilizadas** | `Invoke-WebRequest` contra `http://127.0.0.1:8000/` (servidor activo HTTP 200) y cliente de pruebas de Django (`django.test.Client` con y sin `enforce_csrf_checks=True`) desde `manage.py shell` para recorridos multi-sesión, concurrencia entre pestañas e inspección exacta de respuestas HTTP y estado en base de datos. |

---

## 1. Resumen ejecutivo

Se ejecutaron **49 escenarios de prueba** distribuidos en **35 escenarios por persona** (`A1–A12`, `B1–B9`, `C1–C14`), **7 cadenas de coherencia entre roles** (Sección 5) y **7 bloques de seguridad y robustez** (Sección 6).

| Métrica | Cantidad |
|---|---|
| **Total de escenarios ejecutados** | **49 / 49** (0 no ejecutados) |
| **Escenarios que pasan sin observaciones (OK)** | **16** |
| **Escenarios con fallos, inconsistencias o problemas de usabilidad (FALLA)** | **33** |

### Hallazgos por severidad

| Severidad | Cantidad | IDs de hallazgos |
|---|---|---|
| **Crítica** (Errores 500, tracebacks, pérdida de integridad en BD o mensajes técnicos en inglés/UUID) | **6** | `HAL-001`, `HAL-002`, `HAL-003`, `HAL-004`, `HAL-005`, `HAL-006` |
| **Alta** (Funciones rotas o engañosas, datos invisibles en tablas, inconsistencias entre módulos Ventas ↔ Inventario, autodestrucción de rol Admin, falta de idempotencia) | **11** | `HAL-007`, `HAL-008`, `HAL-009`, `HAL-010`, `HAL-011`, `HAL-012`, `HAL-013`, `HAL-014`, `HAL-015`, `HAL-016`, `HAL-017` |
| **Media** (Validaciones de negocio ausentes en RUC/nombres/lotes/contraseñas, pérdida de selección al fallar formulario, permisos incoherentes entre menú y vistas) | **11** | `HAL-018`, `HAL-019`, `HAL-020`, `HAL-021`, `HAL-022`, `HAL-023`, `HAL-024`, `HAL-025`, `HAL-026`, `HAL-027`, `HAL-028` |
| **Baja** (errores 404 en inglés, jerga técnica sin ayuda contextual, detalles de formato) | **5** | `HAL-029`, `HAL-030`, `HAL-031`, `HAL-032`, `HAL-033` |
| **Total de hallazgos documentados** | **33** | `HAL-001` a `HAL-033` |

> [!IMPORTANT]
> **Contraste con `AUDITORIA_USABILIDAD_05NOV2026.md`:** Los huecos reportados como "cerrados" en las rondas 1 a 4 de la auditoría previa (`HUECO-01` a `HUECO-10`) resolvieron la navegación básica y las migraciones faltantes, pero introdujeron o dejaron expuestos **5 errores 500 nuevos** (`HAL-001` a `HAL-005`), **tablas con columnas en blanco** (`HAL-008`, `HAL-010`), **corrupción retroactiva del historial de cargas iniciales al hacer ajustes positivos** (`HAL-007`) y **ausencia total de las ventas en el historial de movimientos de inventario** (`HAL-009`).

---

## 2. Hallazgos

### HAL-001 — Error 500 (`FieldError`) al filtrar por correlativo en el Historial de ventas
- **Severidad:** Crítica
- **Rol / persona:** Administrador (Ana) y Vendedor (Carmen)
- **Escenario:** A11, C11, Cadena 1 (Sección 5), Sección 6
- **Pasos para reproducir:**
  1. Iniciar sesión como Administrador o Vendedor.
  2. Ir a `/ventas/historial/`.
  3. Escribir cualquier texto en el campo **Correlativo** (por ejemplo `V-00000001` o `%`) y pulsar **Filtrar**.
- **Esperado (para una persona sin conocimientos):** Que la tabla muestre la venta `V-00000001` o indique que no hay coincidencias.
- **Real (texto exacto del mensaje, código HTTP):** Respuesta **HTTP 500 Internal Server Error**. Excepción en servidor:
  `django.core.exceptions.FieldError: Cannot resolve keyword 'correlativo' into field. Choices are: base_amount, cash_received, cash_shift, cash_shift_id, change_given, confirmed_at, correlative, discount_amount, draft, draft_id, id, idempotency_key, igv_amount, lines, seller, seller_id, total_amount`
- **Evidencia:** `GET /ventas/historial/?correlativo=V-00000001` → `500` en `sales/views.py::sales_history`. El modelo `Sale` define el campo en inglés (`correlative`), pero la vista filtra con `correlativo__icontains`.
- **Tipo:** Bug
- **HU / planificación relacionada:** `HU-VEN-05b` (Sprint 2 — declarada ✅ Completada)
- **Sugerencia de corrección:** Cambiar `sales.filter(correlativo__icontains=correlativo)` por `sales.filter(correlative__icontains=correlativo)` en `sales/views.py`.

---

### HAL-002 — Error 500 (`ValidationError`) al ingresar una fecha inválida en el Historial de ventas
- **Severidad:** Crítica
- **Rol / persona:** Administrador (Ana) y Vendedor (Carmen)
- **Escenario:** Sección 6 (`?fecha=hoy`, `?fecha=2026-13-45`)
- **Pasos para reproducir:**
  1. Abrir `/ventas/historial/?fecha=hoy` o `/ventas/historial/?fecha=2026-13-45` (o escribir una fecha inválida en navegadores que no fuercen `type="date"`).
- **Esperado:** Que muestre un aviso amable ("La fecha ingresada no es válida") o ignore el filtro inválido mostrando la lista.
- **Real:** Respuesta **HTTP 500 Internal Server Error**. Excepción no capturada en `sales/views.py`, línea 205 (`sales = sales.filter(confirmed_at__date=fecha)`):
  `django.core.exceptions.ValidationError: ['“hoy” : el valor tiene un formato de fecha inválido. Debería estar en el formato YYYY-MM-DD.']`
- **Evidencia:** `GET /ventas/historial/?fecha=hoy` → `500`; `GET /ventas/historial/?fecha=2026-13-45` → `500`.
- **Tipo:** Bug / Robustez
- **HU / planificación relacionada:** `HU-VEN-05b` (Sprint 2)
- **Sugerencia de corrección:** Validar `fecha` con `django.utils.dateparse.parse_date(fecha)` antes de consultar el ORM; si devuelve `None`, mostrar mensaje de error amigable y no filtrar.

---

### HAL-003 — Error 500 (`ValueError` / `OverflowError`) en Vencimientos de productos cuando `dias` está vacío, tiene letras o es muy grande
- **Severidad:** Crítica
- **Rol / persona:** Administrador (Ana) y Almacenero (Bruno)
- **Escenario:** B5, Cadena 6 (Sección 5), Sección 6
- **Pasos para reproducir:**
  1. Ir a `/productos/vencimientos/`.
  2. Borrar el número `30` del campo "Mostrar lotes que vencen en los próximos días" y pulsar **Filtrar** (`GET /productos/vencimientos/?dias=`), o ingresar `abc` (`?dias=abc`), o un número grande como `999999999` (`?dias=999999999`).
- **Esperado:** Si se envía vacío, asumir 30 días o pedir un número válido; si es texto o un número excesivo, mostrar un error de validación en español.
- **Real:** Respuesta **HTTP 500 Internal Server Error** en los tres casos:
  - Con `?dias=` o `?dias=abc`: `ValueError: invalid literal for int() with base 10: ''` / `'abc'` en `catalog/views.py`, línea 146 (`days = int(request.GET.get("dias", 30))`).
  - Con `?dias=999999999`: `OverflowError: date value out of range` en `catalog/views.py`, línea 147 (`cutoff = today + timezone.timedelta(days=days)`).
  - Además, con `?dias=-5` acepta días negativos sin advertir nada y calcula una fecha de corte en el pasado (`Fecha de corte: 31 de octubre de 2026`).
- **Evidencia:** `GET /productos/vencimientos/?dias=` → `500`; `GET /productos/vencimientos/?dias=abc` → `500`; `GET /productos/vencimientos/?dias=999999999` → `500`.
- **Tipo:** Bug / Robustez
- **HU / planificación relacionada:** `HU-PROD-06` (Sprint 2 — declarada ✅ Completada)
- **Sugerencia de corrección:** Validar que `dias` sea un entero entre `1` y `3650`; en caso contrario usar el valor por defecto (`30`) y mostrar un aviso claro.

---

### HAL-004 — Error 500 (`ValidationError` de UUID) al pasar `?lote=` o `lot_id` no-UUID en Ajuste físico y en Registrar merma
- **Severidad:** Crítica
- **Rol / persona:** Administrador (Ana) y Almacenero (Bruno)
- **Escenario:** A9, B3, Sección 6
- **Pasos para reproducir:**
  1. Como Admin, abrir `/inventario/ajustes/nuevo/?lote=zzz` o enviar `POST /inventario/ajustes/nuevo/` con `lot_id=zzz`.
  2. Como Almacenero, abrir `/inventario/bajas/nueva/?lote=zzz` o enviar `POST /inventario/bajas/nueva/` con `lot_id=zzz`.
- **Esperado:** Respuesta 404 o mensaje en pantalla indicando que el lote seleccionado no existe.
- **Real:** Respuesta **HTTP 500 Internal Server Error** por `django.core.exceptions.ValidationError: ['“zzz” no es un UUID válido.']` al llamar a `get_object_or_404(Lot, pk=lot_id)` sin validar que el parámetro sea un UUID válido.
- **Evidencia:**
  - `GET /inventario/ajustes/nuevo/?lote=zzz` → `500`
  - `POST /inventario/ajustes/nuevo/` (`lot_id=zzz`) → `500`
  - `GET /inventario/bajas/nueva/?lote=zzz` → `500`
  - `POST /inventario/bajas/nueva/` (`lot_id=zzz`) → `500`
- **Tipo:** Bug / Robustez
- **HU / planificación relacionada:** `HU-INV-02`, `HU-INV-03` (Sprint 3)
- **Sugerencia de corrección:** Validar con `uuid.UUID(str(val))` o capturar `(ValueError, ValidationError)` devolviendo `Http404`.

---

### HAL-005 — Error 500 (`OverflowError: Python int too large to convert to SQLite INTEGER`) en Ajuste físico y Carga inicial con cantidades grandes
- **Severidad:** Crítica
- **Rol / persona:** Administrador (Ana) y Almacenero (Bruno)
- **Escenario:** A9, B2
- **Pasos para reproducir:**
  1. Como Admin en `/inventario/ajustes/nuevo/`, ingresar un ajuste (`delta`) muy grande (ej. `99999999999999999999`) y confirmar.
  2. Como Almacenero en `/inventario/carga-inicial/`, ingresar una cantidad de `99999999999999999` (17 dígitos): el sistema la guarda sin límite máximo (`Existencias físicas: 99999999999999999 UND`), y si supera los 64 bits lanza `OverflowError` (500).
- **Esperado:** Que los formularios de inventario tengan un tope razonable (por ejemplo `max_value=1000000`) y muestren "Asegúrese de que este valor sea menor o igual a...".
- **Real:** En `/inventario/ajustes/nuevo/` produce **HTTP 500 Internal Server Error** (`OverflowError: Python int too large to convert to SQLite INTEGER` en `inventory/services.py`, línea 234). En `/inventario/carga-inicial/` permite registrar `99999999999999999` latas en un lote, deformando todas las tablas de stock y vencimientos.
- **Evidencia:** `POST /inventario/ajustes/nuevo/` con `delta=99999999999999999999` → `500`. `POST /inventario/carga-inicial/` con `lots-0-quantity=99999999999999999` → `302` (guardado en BD).
- **Tipo:** Bug / Validación
- **HU / planificación relacionada:** `HU-INV-01` (Sprint 1), `HU-INV-03` (Sprint 3)
- **Sugerencia de corrección:** Definir `max_value=999999` (o el límite operativo de la bodega) en los `IntegerField` de formularios de carga inicial, merma y ajuste físico.

---

### HAL-006 — Exposición de jerga técnica (`“zzz” no es un UUID válido`) y códigos internos de rol (`ADMIN`, `ALMACENERO`, `VENDEDOR`) en formularios
- **Severidad:** Crítica (según regla de Sección 2: *texto en inglés/técnico o nombres de campos/tipos de BD es severidad Crítica*)
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A3, A4, A5
- **Pasos para reproducir:**
  1. En `/productos/nuevo/`, enviar un valor alterado en `category` (`category=zzz`): el formulario responde en pantalla `“zzz” no es un UUID válido.`
  2. En `/empleados/nuevo/` y `/empleados/<id>/editar/`, abrir el desplegable **Rol**: las opciones visibles son los códigos internos en mayúsculas `ADMIN`, `ALMACENERO`, `VENDEDOR` en lugar de los nombres legibles (`Administrador`, `Almacenero`, `Vendedor`) que sí se muestran en la tabla de `/empleados/`.
  3. En `/empleados/nuevo/`, al ingresar una contraseña de 4 caracteres (`1234`), el mensaje sale pegado sin espacio: `Asegúrese de que este valor tenga al menos 8 carácter(es) (tiene4).`
- **Esperado:** Mensajes sin términos como `UUID` y nombres de rol legibles ("Administrador", "Almacenero", "Vendedor").
- **Real:** `“zzz” no es un UUID válido.` (HTTP 200) y opciones `<option value="3">ADMIN</option>`, `<option value="4">ALMACENERO</option>`, `<option value="5">VENDEDOR</option>`.
- **Evidencia:** `POST /productos/nuevo/` (`category=zzz`) → `200`; `GET /empleados/nuevo/` → `200`.
- **Tipo:** Usabilidad / Textos técnicos
- **HU / planificación relacionada:** `HU-PROD-02`, `HU-USR-02`, `HU-USR-03`
- **Sugerencia de corrección:** Personalizar `error_messages={'invalid_choice': 'Seleccione una categoría válida.'}` en el `ModelChoiceField` y mostrar `role.name` en el `__str__` del modelo `Role` o en `label_from_instance`.

---

### HAL-007 — Ajuste físico positivo sobrescribe `initial_quantity` del lote y falsifica retroactivamente la "Carga inicial" en el historial de movimientos
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana) y Almacenero (Bruno)
- **Escenario:** A9, B6, Cadena 1 (Sección 5)
- **Pasos para reproducir:**
  1. Como Almacenero, registrar carga inicial del producto `Prod Test 15` con el `Lote A2` por **20 unidades**.
  2. Ir a `/inventario/productos/<id>/movimientos/`: se observa `05/11/2026 02:19 | ▲ Entrada | Carga inicial — Lote A2 | +20 | Sistema`.
  3. Como Admin, ir a `/inventario/ajustes/nuevo/` y registrar un ajuste físico positivo de **+2 unidades** sobre `Lote A2` (`motivo: conteo fisico`).
  4. Volver a `/inventario/productos/<id>/movimientos/`.
- **Esperado:** Que la línea histórica `Carga inicial — Lote A2` conserve su cantidad original (`+20`) y aparezca además la línea `⇅ Ajuste | Ajuste físico — Lote A2 | +2`.
- **Real:** El ajuste físico positivo modifica `lot.initial_quantity` en la base de datos de `20` a `22`. Como consecuencia, la vista de movimientos muestra **ambas cosas**:
  - `05/11/2026 02:23 | ⇅ Ajuste | Ajuste físico — Lote A2. conteo fisico | +2 | Administrador Demo`
  - `05/11/2026 02:19 | ▲ Entrada | Carga inicial — Lote A2 | +22 | Sistema`
  ¡El historial queda alterado retroactivamente y la suma de entradas aparenta ser `22 + 2 = 24` en vez de `22`! Además, el responsable de la carga inicial aparece siempre como `Sistema` en lugar de `Almacenero Demo` (`initial_load.responsible`).
- **Evidencia:** `GET /inventario/productos/<id>/movimientos/` → `200`; inspección en BD: `Lot.objects.get(number='A2').initial_quantity == 22`.
- **Tipo:** Bug / Inconsistencia entre módulos
- **HU / planificación relacionada:** `HU-INV-03` (Sprint 3), `HU-INV-06` (Post-Sprint, `AUDITORIA_USABILIDAD_05NOV2026.md` §13)
- **Sugerencia de corrección:** No modificar `lot.initial_quantity` durante `register_physical_adjustment` (eliminar o ajustar el `CheckConstraint` que obliga `available_quantity <= initial_quantity`), y mostrar `lot.initial_load.responsible.display_name` en lugar de `"Sistema"` en `product_movements`.

---

### HAL-008 — Las columnas "Correlativo" y "Vuelto" aparecen completamente en blanco en `/ventas/historial/` y `/ventas/historial/turno/`
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana) y Vendedor (Carmen)
- **Escenario:** A11, C11, Cadena 1 y Cadena 3 (Sección 5)
- **Pasos para reproducir:**
  1. Realizar una venta (ej. `V-00000002`, total `S/ 32,30`, efectivo recibido `S/ 50,00`, vuelto `S/ 17,70`).
  2. Como Vendedor, abrir **Mis ventas del turno** (`/ventas/historial/turno/`).
  3. Como Admin (o Vendedor), abrir **Historial de ventas** (`/ventas/historial/`).
- **Esperado:** Ver en cada fila el número de correlativo (`V-00000002`) como enlace clicable a la constancia y el vuelto entregado (`17,70`).
- **Real:** En ambas tablas, el enlace `<a href="/ventas/constancia/<uuid>/"></a>` está **vacío** (sin texto visible, por lo que no se puede hacer clic en él) y la celda **Vuelto** está **vacía** (`<td class="text-end"></td>`).
- **Evidencia:** HTML devuelto por `GET /ventas/historial/turno/` y `GET /ventas/historial/`:
  ```html
  <td class="font-monospace">
    <a href="/ventas/constancia/21d705a3-2e96-4992-bf1b-b8671958c41c/"></a>
  </td>
  <td>05/11/2026 02:18</td>
  <td class="text-end">32,30</td>
  <td class="text-end">50,00</td>
  <td class="text-end"></td>
  ```
  Los templates referencian atributos en español (`sale.correlativo`, `sale.vuelto`) que no existen en el modelo `Sale` (`correlative`, `change_given`).
- **Tipo:** Bug
- **HU / planificación relacionada:** `HU-VEN-05a`, `HU-VEN-05b` (Sprint 2 — declaradas ✅ Completadas)
- **Sugerencia de corrección:** En `sales_shift_history.html` y `sales_history.html`, reemplazar `{{ sale.correlativo }}` por `{{ sale.correlative }}` y `{{ sale.vuelto }}` por `{{ sale.change_given }}`.

---

### HAL-009 — Los movimientos de un producto (`/inventario/productos/<id>/movimientos/`) NO incluyen las ventas realizadas
- **Severidad:** Alta
- **Rol / persona:** Almacenero (Bruno) y Administrador (Ana)
- **Escenario:** B6, Cadena 1 (Sección 5)
- **Pasos para reproducir:**
  1. El producto `Atun en lata 170g` inicia con carga inicial de `+60` unidades (y una venta demo previa de 2 unidades, quedando en 58).
  2. La Vendedora Carmen vende 5 unidades más en `V-00000002`. El stock físico baja a **53 unidades**.
  3. El Almacenero Bruno entra a `/inventario/productos/066b12d2-c9d5-4fa5-b4b6-3ae413988ba8/movimientos/` para entender por qué hay 53 unidades en vez de 60.
- **Esperado:** Que la tabla de movimientos liste las salidas por venta (`▼ Venta V-00000001 (-2)` y `▼ Venta V-00000002 (-5)`) de modo que la suma de movimientos cuadre con el `Stock físico actual: 53 unid.`.
- **Real:** La pantalla dice arriba `Stock físico actual: 53 unid.`, pero la tabla solo muestra una fila:
  `05/11/2026 01:54 | ▲ Entrada | Carga inicial — Lote A1 | +60 | Sistema`
  Las ventas no aparecen en absoluto. Además, el modelo `SaleLine` ni siquiera guarda de qué lote se descontó cada venta, solo guarda un snapshot del nombre y código de barras (`product_snapshot_barcode`).
- **Evidencia:** `GET /inventario/productos/066b12d2-c9d5-4fa5-b4b6-3ae413988ba8/movimientos/` → `200`.
- **Tipo:** Inconsistencia entre módulos (Ventas ↔ Inventario)
- **HU / planificación relacionada:** `HU-INV-06` (Post-Sprint, `AUDITORIA_USABILIDAD_05NOV2026.md` §13, donde se afirma que unifica movimientos pero omite ventas)
- **Sugerencia de corrección:** Incluir las líneas de venta (`SaleLine` filtradas por `product_snapshot_barcode=product.barcode`) en `product_movements` como salidas (`▼ Venta`), o registrar movimientos por lote al ejecutar `checkout_sale`.

---

### HAL-010 — La pantalla Vencimientos de productos (`/productos/vencimientos/`) muestra `—` en la columna "Lote / Nro." para todos los lotes y no tiene enlace en el menú
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana) y Almacenero (Bruno)
- **Escenario:** B5, Cadena 5 y Cadena 6 (Sección 5)
- **Pasos para reproducir:**
  1. Iniciar sesión como Admin o Almacenero: observar que `/productos/vencimientos/` **no aparece en el menú lateral de ningún rol** (sigue inaccesible salvo escribiendo la URL a mano, tal como se señaló en `AUDITORIA_USABILIDAD_05NOV2026.md` §4 y §9).
  2. Abrir directamente `/productos/vencimientos/`.
- **Esperado:** Ver el código de cada lote próximo a vencer (ej. `C1`, `Z1`, `L1`) en la columna **Lote / Nro.**.
- **Real:** Todas las filas muestran `—` en la columna **Lote / Nro.**:
  `Frejoles en lata 400g | Productos enlatados | — | 17 de noviembre de 2026 | 23 | Próximo`
- **Evidencia:** `GET /productos/vencimientos/` → `200`. El template busca un nombre de atributo distinto a `lot.number`.
- **Tipo:** Bug / Usabilidad
- **HU / planificación relacionada:** `HU-PROD-06` (Sprint 2 — declarada ✅ Completada)
- **Sugerencia de corrección:** Usar `{{ lot.number }}` en el template de vencimientos y agregar el enlace a `/productos/vencimientos/` en el menú lateral de Admin y Almacenero.

---

### HAL-011 — El Administrador puede cambiar su propio rol a Vendedor/Almacenero en `/empleados/<id>/editar/`, perdiendo acceso de inmediato y dejando al sistema sin ningún Administrador activo
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A4
- **Pasos para reproducir:**
  1. Iniciar sesión como el único Administrador activo (`admin.demo@pmv.invalid`).
  2. Ir a `/empleados/`: verificar que para la propia cuenta sí se oculta el botón `Desactivar` y que `POST /empleados/<id>/estado/` bloquea correctamente con `"No puedes desactivar tu propia cuenta."`.
  3. Sin embargo, hacer clic en **Editar** sobre la propia fila (`/empleados/ef845663-9b4b-48ea-bf39-ffde99a662b6/editar/`), cambiar el campo **Rol** a `VENDEDOR` y pulsar **Guardar cambios**.
- **Esperado:** Que el sistema impida que el Administrador cambie su propio rol (o impida degradar al último Administrador activo del sistema).
- **Real:** El cambio se guarda (`302 -> /empleados/`) e **inmediatamente la redirección a `/empleados/` devuelve `403 Acceso denegado`** porque Ana ya no es Administradora. El sistema queda con **0 administradores activos** y nadie puede volver a entrar a `/empleados/` para revertirlo.
- **Evidencia:** `POST /empleados/ef845663-9b4b-48ea-bf39-ffde99a662b6/editar/` con `role=5` (`VENDEDOR`) → `302 /empleados/` → `GET /empleados/` devuelve `403`.
- **Tipo:** Bug de lógica de negocio / Seguridad
- **HU / planificación relacionada:** `HU-USR-03` (Sprint 3)
- **Sugerencia de corrección:** Impedir en `employee_edit` que un usuario modifique su propio rol o que el último `ADMIN` activo cambie de rol.

---

### HAL-012 — Al deshabilitar un producto mientras un vendedor lo tiene en su venta en preparación, el intento de cobro falla silenciosamente sin ningún mensaje de error
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana) y Vendedora (Carmen)
- **Escenario:** A7, C8, Cadena 4 (Sección 5)
- **Pasos para reproducir:**
  1. Carmen (Vendedora) agrega 2 unidades de `Atun en lata 170g` a su borrador y entra a `/ventas/cobrar/`.
  2. Ana (Admin) deshabilita `Atun en lata 170g` desde `/productos/` (`POST /productos/<id>/disponibilidad/`).
  3. Carmen ingresa `Efectivo recibido: 50` en `/ventas/cobrar/` y pulsa **Confirmar cobro**.
- **Esperado:** Que la pantalla muestre un mensaje claro: *"El producto «Atun en lata 170g» ya no está disponible para la venta. Quítalo de la venta en preparación para continuar."*
- **Real:** La petición `POST /ventas/cobrar/` devuelve `HTTP 200` recargando la misma pantalla `/ventas/cobrar/` **sin ningún mensaje de error visible en todo el HTML** (ni alerta superior ni error en campos). Carmen aprieta "Confirmar cobro" una y otra vez y no pasa absolutamente nada ni sabe por qué no puede cobrar.
- **Evidencia:** `POST /ventas/cobrar/` con `cash_received=50` cuando el producto del borrador tiene `is_active=False` → `200 OK`, lista de alertas/errores en el DOM: `[]`.
- **Tipo:** Bug / Usabilidad crítica en mostrador
- **HU / planificación relacionada:** `HU-PROD-05` (Sprint 2), `HU-VEN-01c` (Sprint 1)
- **Sugerencia de corrección:** En `sales_checkout`, asegurarse de renderizar en el template la excepción de negocio o `messages.error` cuando un producto del borrador está inactivo.

---

### HAL-013 — El Administrador tiene bloqueado el acceso (`403 Acceso denegado`) a las Constancias de venta (`/ventas/constancia/<id>/`) pese a que el Historial de ventas las enlaza
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A11, C9, Cadena 1 (Sección 5)
- **Pasos para reproducir:**
  1. Iniciar sesión como Administrador (`admin.demo@pmv.invalid`).
  2. Ir a `/ventas/historial/`, donde cada fila incluye un enlace `<a href="/ventas/constancia/<uuid>/">`.
  3. Abrir `/ventas/constancia/<uuid>/` de cualquier venta.
- **Esperado:** Que el Administrador pueda ver el detalle/constancia de las ventas de su negocio.
- **Real:** Devuelve **HTTP 403 (`Acceso denegado — No tienes permiso para esta operación`)** porque la vista `sales_receipt` solo autoriza al rol `VENDEDOR`.
- **Evidencia:** `GET /ventas/constancia/21d705a3-2e96-4992-bf1b-b8671958c41c/` como Admin → `403`.
- **Tipo:** Bug de permisos / Inconsistencia entre roles
- **HU / planificación relacionada:** `HU-VEN-02a` (Sprint 1), `HU-VEN-05b` (Sprint 2)
- **Sugerencia de corrección:** Permitir el rol `ADMIN` en el decorador de autorización de `sales_receipt` (sin exigir que sea el `seller` propietario cuando quien consulta es `ADMIN`).

---

### HAL-014 — Fuga de información entre vendedores en `/ventas/historial/` y bloqueo para reabrir constancias de turnos anteriores
- **Severidad:** Alta
- **Rol / persona:** Vendedora (Carmen y otros vendedores)
- **Escenario:** C9, Cadena 5 (Sección 5), Sección 6
- **Pasos para reproducir:**
  1. Iniciar sesión con un segundo vendedor (`t1@pmv.invalid`) que no ha hecho ninguna venta.
  2. Abrir `/ventas/constancia/<id>/` de una venta de `Vendedor Demo`: devuelve `404` (correcto, protege la constancia).
  3. Abrir `/ventas/historial/`: devuelve **200 OK** y muestra todas las ventas de todos los vendedores (`Vendedor Demo`, montos, horas y cajas).
- **Esperado:** Si el menú del Vendedor solo ofrece **Mis ventas del turno** (`/ventas/historial/turno/`), un vendedor no debería poder consultar el historial global de todos los vendedores en `/ventas/historial/`, o bien las reglas de visibilidad deberían ser consistentes.
- **Real:** `/ventas/historial/` está abierto a cualquier `VENDEDOR`, permitiéndole ver cuánto vendieron sus compañeros.
- **Evidencia:** `GET /ventas/historial/` con `t1@pmv.invalid` (rol `VENDEDOR`) → `200 OK` mostrando las ventas de `Vendedor Demo`.
- **Tipo:** Seguridad / Autorización
- **HU / planificación relacionada:** `HU-VEN-05a`, `HU-VEN-05b` (Sprint 2)
- **Sugerencia de corrección:** Restringir `/ventas/historial/` al rol `ADMIN` (o filtrar por `seller=request.user` si el rol es `VENDEDOR`).

---

### HAL-015 — Doble envío en Registrar merma (`/inventario/bajas/nueva/`) y en Ajuste físico (`/inventario/ajustes/nuevo/`) descuenta o suma el stock dos veces
- **Severidad:** Alta
- **Rol / persona:** Almacenero (Bruno) y Administrador (Ana)
- **Escenario:** A9, B3
- **Pasos para reproducir:**
  1. Como Almacenero, seleccionar el `Lote A2` de `Prod Test 15` (disponible: `15 u.`), ingresar `Cantidad a dar de baja: 3`, `Motivo: Daño o rotura`, `Detalle: latas abolladas`.
  2. Enviar el formulario dos veces seguidas (doble clic en **Confirmar baja**).
- **Esperado:** Que el segundo envío sea detectado como duplicado y solo se descuenten 3 unidades en total.
- **Real:** A diferencia de `/ventas/cobrar/` (que sí tiene `idempotency_key`), los formularios de mermas y ajustes físicos **carecen de token de idempotencia**. Las dos peticiones se procesan con éxito (`302 -> /inventario/bajas/nueva/`), generando dos bajas correlativas y descontando **6 unidades** en lugar de 3 (el disponible pasa de `15` → `12` → `9`).
- **Evidencia:** `POST /inventario/bajas/nueva/` × 2 → `disp=12, mermas=2` y luego `disp=9, mermas=3`. Ambos aparecen duplicados en `/inventario/productos/<id>/movimientos/`.
- **Tipo:** Bug / Concurrencia
- **HU / planificación relacionada:** `HU-INV-02`, `HU-INV-03` (Sprint 3)
- **Sugerencia de corrección:** Incorporar un campo oculto `idempotency_key` (UUID por renderizado del formulario) en `StockWriteOff` y `PhysicalAdjustment`, igual que en `Sale`.

---

### HAL-016 — Inconsistencias en alertas de stock y vencimientos (`/inicio/` vs `/inventario/stock/`)
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana) y Almacenero (Bruno)
- **Escenario:** A11, B5, Cadena 6 (Sección 5)
- **Pasos para reproducir:**
  1. **Lote vencido duplicado en dos alertas opuestas:** Cuando un lote ya venció (ej. `Prod Test 19 — Lote Z1 — 5 unid. — Venció: 31 de octubre de 2026`), en `/inventario/stock/` aparece simultáneamente en `⚠ Lotes VENCIDOS con stock disponible (1)` **y también** en `⏳ Lotes próximos a vencer (dentro de 30 días) — 4`. Además, el contador `Lotes por vencer (30 días)` del Resumen del Admin (`/inicio/`) también cuenta los lotes ya vencidos (`4`).
  2. **Producto con todas sus unidades vencidas figura como `Estado: OK`:** `Prod Test 19` tiene `Stock físico: 5`, `Stock vendible: 0` (porque las 5 están vencidas) y `Mínimo: 3`. Sin embargo, la columna **Estado** dice `OK` y no aparece en la alerta de `Stock bajo el mínimo`, porque la alerta compara el `Stock físico` (5 >= 3) en lugar del `Stock vendible` (0 < 3).
  3. **Desfase entre `/inicio/` y `/inventario/stock/` al deshabilitar un producto:** Al deshabilitar `Duraznos en almibar 820g` (stock 4 / mín 10), el contador `Productos con stock bajo` en `/inicio/` baja de `8` a `7`, pero al hacer clic en `Ver inventario y alertas` (`/inventario/stock/`), el panel sigue diciendo `🔶 Stock bajo el mínimo (8 productos)` e incluye productos deshabilitados sin indicar que están inactivos.
  4. **Inconsistencia con `minimum_stock=0`:** Si un producto se crea con `Existencia mínima: 0` y tiene `0` unidades (`Prod Test 7`), en `/inventario/stock/` la tabla dice `Estado: Sin stock`, pero el panel superior de alertas `Stock bajo el mínimo` y el contador de `/inicio/` **no lo cuentan** (comparan `stock < minimum_stock` en vez de alertar productos sin stock).
- **Esperado:** Que un lote vencido no se cuente como "próximo a vencer", que la alerta de stock bajo evalúe el stock vendible de productos activos y que el número de `/inicio/` coincida exactamente con el de `/inventario/stock/`.
- **Real:** Los contadores y criterios difieren entre `/inicio/` y `/inventario/stock/`.
- **Evidencia:** Salida verificada en `GET /inicio/` (`Productos con stock bajo 7`) vs `GET /inventario/stock/` (`Stock bajo el mínimo (8 productos)` y `Lote Z1` repetido en ambos paneles).
- **Tipo:** Inconsistencia entre módulos / Bug de lógica
- **HU / planificación relacionada:** `HU-INV-04`, `HU-INV-05`, `HU-REP-01` (Post-Sprint, `AUDITORIA_USABILIDAD_05NOV2026.md` §13–14)
- **Sugerencia de corrección:** Filtrar lotes por vencer con `expiration_date__gte=today, expiration_date__lte=today+30d`; evaluar stock bajo sobre `stock_vendible < minimum_stock` filtrando `is_active=True` tanto en `_admin_summary` como en `stock_overview`.

---

### HAL-017 — El Historial de turnos (`/caja/turnos/`) oculta el monto esperado, el monto contado y la diferencia (faltante/sobrante) de los turnos cerrados
- **Severidad:** Alta
- **Rol / persona:** Administrador (Ana) y Vendedora (Carmen)
- **Escenario:** A11, C12, Cadena 3 (Sección 5)
- **Pasos para reproducir:**
  1. Como Vendedora, cerrar un turno con un faltante de `S/ -12,30` (Esperado `S/ 242,30`, Contado `S/ 230,00`) o con cuadre exacto (`S/ 193,90`). En la pantalla inmediata posterior al cierre (`/caja/turnos/<id>/cerrado/`) sí se ve el acta con `Monto esperado`, `Monto contado` y `Diferencia`.
  2. Ir después a **Historial de turnos** (`/caja/turnos/`) como Administrador o Vendedora.
- **Esperado:** Que el Administrador pueda auditar en `/caja/turnos/` con cuánto cerró cada turno, cuánto debía haber y si hubo faltante o sobrante (o al menos hacer clic para ver el Acta de cierre).
- **Real:** La tabla de `/caja/turnos/` solo muestra 6 columnas: `Caja | Vendedor | Apertura | Monto inicial | Cierre | Estado`, sin mostrar `Monto esperado`, `Monto contado`, `Diferencia` ni enlace al acta `/caja/turnos/<id>/cerrado/`, a pesar de que la vista hace `prefetch_related("close")`.
- **Evidencia:** `GET /caja/turnos/` → `CAJA-01 | Vendedor Demo | 05/11/2026 01:31 | S/ 200,00 | 05/11/2026 02:18 | Cerrado`.
- **Tipo:** Falta de funcionalidad en UI / Inconsistencia entre roles
- **HU / planificación relacionada:** `HU-CAJA-02` (Sprint 1), `HU-CAJA-05` (Sprint 2 — declarada ✅ Completada)
- **Sugerencia de corrección:** Agregar las columnas `Esperado`, `Contado` y `Diferencia` (y enlace a `/caja/turnos/<id>/cerrado/`) en `cash/templates/cash/cash_shift_history.html`.

---

### HAL-018 — Desactivar a un Vendedor con turno abierto deja la única caja (`CAJA-01`) bloqueada permanentemente para todos los demás vendedores
- **Severidad:** Media
- **Rol / persona:** Administrador (Ana) y Vendedores (Carmen / Nuevo vendedor)
- **Escenario:** A4, C2, Cadena 4 (Sección 5)
- **Pasos para reproducir:**
  1. `Vendedor Demo` tiene abierto el turno en `CAJA-01`.
  2. El Administrador va a `/empleados/` y pulsa **Desactivar** sobre `Vendedor Demo` (`POST /empleados/<id>/estado/`).
  3. El sistema desactiva la cuenta sin advertir que tiene un turno abierto ni cerrarlo. `Vendedor Demo` es expulsado en su siguiente clic (`302 -> /?next=/ventas/`).
  4. Otro vendedor activo (`t1@pmv.invalid`) entra y trata de abrir turno en `/caja/abrir/`.
- **Esperado:** Que al intentar desactivar a un vendedor con turno abierto el sistema exija cerrar primero el turno (o permita al Admin forzar el cierre), para no inutilizar la caja.
- **Real:** El nuevo vendedor recibe el error `"Ya existe un turno abierto. Cierre ese turno antes de abrir otro."`, el Administrador recibe `403` si intenta entrar a `/caja/cerrar/`, y el vendedor dueño del turno no puede iniciar sesión porque está inactivo. El minimarket queda sin poder vender hasta que el Admin adivine que debe reactivar al vendedor anterior para que cierre su turno.
- **Evidencia:** `POST /empleados/d4186854-8e1e-4a70-81c5-4bcb10382664/estado/` → `302`; `CashShift.objects.filter(status='OPEN').count() == 1`; segundo vendedor en `POST /caja/abrir/` → `"Ya existe un turno abierto. Cierre ese turno antes de abrir otro."`.
- **Tipo:** Bug de flujo de negocio
- **HU / planificación relacionada:** `HU-USR-04` (Sprint 3), `HU-CAJA-01` (Sprint 1)
- **Sugerencia de corrección:** Impedir desactivar una cuenta de vendedor mientras tenga un `CashShift` en estado `OPEN`, mostrando un mensaje claro al Administrador.

---

### HAL-019 — Carga inicial (`/inventario/carga-inicial/`) pierde el producto seleccionado cuando falla cualquier validación de lotes y muestra un error falso de "Escoja una opción válida"
- **Severidad:** Media
- **Rol / persona:** Almacenero (Bruno)
- **Escenario:** B2
- **Pasos para reproducir:**
  1. Como Almacenero en `/inventario/carga-inicial/`, seleccionar un producto y cometer un error en un lote (ej. cantidad `0`, costo `0` o fecha inválida).
  2. O bien enviar un producto que ya recibió carga inicial en otra pestaña.
- **Esperado:** Que el formulario conserve el producto seleccionado y marque únicamente el error del campo del lote defectuoso.
- **Real:** Cuando el producto ya fue cargado (o cuando se reenvía el formulario tras una carga previa), el desplegable `Producto` recarga el queryset excluyendo productos con carga y muestra un bloque confuso con todos los nombres concatenados seguido de `Escoja una opción válida. Esa opción no está entre las disponibles.` sin explicar que **"Este producto ya tiene una carga inicial registrada"**. Además, por defecto renderiza 4 bloques de lotes (`Lote 1` a `Lote 4`) sin botones dinámicos para agregar más de 4 ni quitar filas visualmente.
- **Evidencia:** `POST /inventario/carga-inicial/` sobre un producto que ya tenía carga inicial → `200 OK` con mensaje `Escoja una opción válida. Esa opción no está entre las disponibles.`.
- **Tipo:** Usabilidad / Validación
- **HU / planificación relacionada:** `HU-INV-01` (Sprint 1)
- **Sugerencia de corrección:** Si el `product_id` enviado pertenece a un producto que ya tiene `InitialInventoryLoad`, devolver el mensaje específico `"Este producto ya cuenta con su carga inicial de existencias."`.

---

### HAL-020 — El Almacenero queda en un callejón operativo para registrar nuevas entradas de mercadería de productos existentes y ve botones en `/inventario/stock/` que le dan error 403
- **Severidad:** Media
- **Rol / persona:** Almacenero (Bruno)
- **Escenario:** B1, B4, Cadena 5 (Sección 5)
- **Pasos para reproducir:**
  1. Bruno (Almacenero) recibe 50 latas nuevas de `Atun en lata 170g` (que ya tuvo su carga inicial).
  2. Entra a **Existencias iniciales** (`/inventario/carga-inicial/`): `Atun en lata 170g` **no aparece en la lista**, y el texto pequeño dice *"Solo aparecen productos activos que todavía no tienen carga inicial"*, sin explicarle cómo ingresar nueva mercadería ni a quién acudir.
  3. Bruno va a **Ver inventario y alertas** (`/inventario/stock/`): al final de la tabla ve tres botones: `+ Registrar existencias iniciales`, `Ajuste físico` (`/inventario/ajustes/nuevo/`) y `Registrar merma`.
  4. Bruno hace clic en **Ajuste físico** creyendo que por ahí se ingresa mercadería.
- **Esperado:** Que `/inventario/stock/` no muestre al Almacenero el botón `Ajuste físico` si es exclusivo del Administrador, y que en `/inventario/carga-inicial/` se explique claramente que en esta versión las entradas posteriores las registra el Administrador mediante Ajuste físico.
- **Real:** Al hacer clic en el botón **Ajuste físico** visible en su propia pantalla de `/inventario/stock/`, Bruno recibe **`403 Acceso denegado`** (`No tienes permiso para esta operación`). Del mismo modo, el Administrador ve en `/inventario/stock/` el botón `+ Registrar existencias iniciales`, que al pulsarlo también le devuelve **`403 Acceso denegado`**.
- **Evidencia:** En `/inventario/stock/` (`inventory/templates/inventory/stock_overview.html`) los 3 botones inferiores se renderizan sin condicional de rol:
  - Admin clic en `+ Registrar existencias iniciales` (`/inventario/carga-inicial/`) → `403`
  - Almacenero clic en `Ajuste físico` (`/inventario/ajustes/nuevo/`) → `403`
- **Tipo:** Usabilidad / Desfase UI vs Permisos
- **HU / planificación relacionada:** `HU-INV-01`, `HU-INV-03`, `HU-INV-04`
- **Sugerencia de corrección:** Condicionar por rol los botones al pie de `stock_overview.html` (`carga-inicial` solo para `ALMACENERO`, `ajustes/nuevo` solo para `ADMIN`) y añadir una nota explicativa en `/inventario/carga-inicial/`.

---

### HAL-021 — El Almacenero puede entrar por URL a `/productos/` y `/inventario/proveedores/` (ocultos en su menú) y ve botones de "Editar", "Deshabilitar" y "+ Nuevo proveedor" que al pulsarlos dan 403
- **Severidad:** Media
- **Rol / persona:** Almacenero (Bruno)
- **Escenario:** B7, B8, Cadena 5 (Sección 5)
- **Pasos para reproducir:**
  1. Iniciar sesión como Almacenero (`almacen.demo@pmv.invalid`).
  2. Observar que su menú lateral solo tiene: `Inicio`, `Ver inventario y alertas`, `Existencias iniciales`, `Registrar merma`. No tiene enlace a Proveedores ni a Productos.
  3. Abrir `/inventario/proveedores/` o `/productos/`: ambas cargan con `HTTP 200`.
  4. En `/inventario/proveedores/` se muestran el botón `+ Nuevo proveedor` y los botones `Desactivar` de cada fila; al pulsarlos, el servidor responde `403 Acceso denegado`.
  5. En `/productos/` se muestran los botones `Editar` y `Deshabilitar` en cada producto; al pulsarlos, responde `403 Acceso denegado`.
- **Esperado:** Si el Almacenero tiene permiso de lectura en Proveedores y Productos, debería tener enlace en su menú lateral y las tablas deberían ocultar los botones de creación/edición/desactivación que son exclusivos del Administrador.
- **Real:** Las pantallas están huérfanas de menú para el Almacenero y muestran controles de acción que fallan con `403`.
- **Evidencia:** `GET /inventario/proveedores/` (Almacenero) → `200` con `href="/inventario/proveedores/nuevo/"`; `GET /inventario/proveedores/nuevo/` (Almacenero) → `403`; `POST /inventario/proveedores/<id>/estado/` (Almacenero) → `403`.
- **Tipo:** Inconsistencia Menú vs Permisos
- **HU / planificación relacionada:** `HU-PROV-01`, `HU-PROD-01`
- **Sugerencia de corrección:** Ocultar en `product_list.html` y `supplier_list.html` los botones de mutación cuando `request.user.role.code != 'ADMIN'`, y decidir si el Almacenero debe tener acceso desde el menú o no.

---

### HAL-022 — Validación de RUC en Proveedores (`/inventario/proveedores/nuevo/`) acepta letras, símbolos y 10 dígitos
- **Severidad:** Media
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A10
- **Pasos para reproducir:**
  1. Ir a `/inventario/proveedores/nuevo/`.
  2. Registrar un proveedor con `RUC: 1234567890` (10 dígitos) → lo guarda (`302`).
  3. Registrar otro proveedor con `RUC: 2012345678A` (con letras) → lo guarda (`302`).
  4. Registrar un proveedor con `Teléfono: abc<script>` → lo guarda (`302`).
- **Esperado:** En Perú, el RUC debe tener exactamente **11 dígitos numéricos** (y el teléfono solo dígitos/espacios/guiones).
- **Real:** El campo `ruc` solo valida `max_length=11` y unicidad, permitiendo RUCs de 1 a 10 caracteres o con letras (`2012345678A`), y `phone` acepta cualquier texto arbitrario.
- **Evidencia:** `POST /inventario/proveedores/nuevo/` con `ruc=1234567890` → `302`; con `ruc=2012345678A` → `302`; con `phone=abc<script>` → `302`.
- **Tipo:** Bug de validación
- **HU / planificación relacionada:** `HU-PROV-02` (Sprint 3)
- **Sugerencia de corrección:** Agregar un `RegexValidator(r'^\d{11}$', 'El RUC debe contener exactamente 11 dígitos numéricos.')` en el modelo/formulario de `Supplier`.

---

### HAL-023 — Creación de Categorías (`/productos/categorias/nueva/`) permite crear categorías que jamás pueden usarse al registrar productos
- **Severidad:** Media
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A8
- **Pasos para reproducir:**
  1. Como Admin, ir a **Categorías** (`/productos/categorias/`) en el menú lateral y pulsar **+ Nueva categoría** (`/productos/categorias/nueva/`).
  2. Crear la categoría `Bebidas XYZ` (o `<b>@#$%</b>`): se guarda con estado `Activa` (`302 -> /productos/categorias/`).
  3. Ir a **Registrar producto** (`/productos/nuevo/`) e intentar elegir la categoría `Bebidas XYZ` recién creada.
- **Esperado:** Si el menú ofrece crear categorías y las marca como `Activa`, que aparezcan en el selector de categoría de `/productos/nuevo/`; o si por restricción de R1 solo se admite "Productos enlatados", que la pantalla de Categorías lo advierta claramente en lugar de dejar crear categorías inútiles.
- **Real:** En `/productos/nuevo/` el selector **Categoría** filtra únicamente `Productos enlatados`; ninguna de las categorías creadas en `/productos/categorias/nueva/` aparece jamás en el selector ni se explica por qué. Además, permite nombres de categoría compuestos solo por símbolos (`<b>@#$%</b>`).
- **Evidencia:** `POST /productos/categorias/nueva/` (`name=Bebidas XYZ`) → `Activa` en `/productos/categorias/`, pero en `GET /productos/nuevo/` las únicas opciones de `<select name="category">` son `['---------', 'Productos enlatados']`.
- **Tipo:** Función que promete algo y no lo cumple / Usabilidad
- **HU / planificación relacionada:** `HU-CAT-01`, `HU-CAT-02` (Sprint 2), `HU-PROD-02` (Sprint 1)
- **Sugerencia de corrección:** Añadir un aviso visible en `/productos/categorias/` y `/productos/categorias/nueva/` indicando que en el alcance actual (R1) el registro de productos opera exclusivamente con la categoría "Productos enlatados".

---

### HAL-024 — Creación de Productos (`/productos/nuevo/`) permite nombres duplicados, códigos de barras con letras/espacios y precios en notación científica (`1e5`)
- **Severidad:** Media
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A5
- **Pasos para reproducir:**
  1. En `/productos/nuevo/`, registrar un producto llamado `ATUN EN LATA 170G` o `  Atun   en lata 170g ` (cuando ya existe `Atun en lata 170g`) con otro código de barras: se guarda (`302`), quedando 3 productos llamados igual en el catálogo y en el buscador de ventas.
  2. Ingresar `Código de barras: ABC123` o `123 456 789`: se guarda con letras o con espacios visibles en las tablas, pese a que el texto de ayuda dice *"Se ignorarán espacios exteriores e internos al compararlo"*.
  3. Ingresar `Precio final con IGV (S/): 1e5`: se guarda con precio `S/ 100000,00`.
  4. Ingresar `Nombre: <b>x</b> "' ;--`: se guarda sin validar caracteres mínimos alfanuméricos.
- **Esperado:** Que no se permitan dos productos con el mismo nombre normalizado, que el código de barras acepte solo dígitos (EAN/UPC) y se guarde sin espacios, y que el precio rechace notación científica.
- **Real:** Todos los casos anteriores devuelven `302` y crean productos en el catálogo.
- **Evidencia:** `POST /productos/nuevo/` con `name='ATUN EN LATA 170G'` → `302`; con `barcode='ABC123'` → `302`; con `sale_price='1e5'` → `302`.
- **Tipo:** Validación de datos
- **HU / planificación relacionada:** `HU-PROD-02` (Sprint 1)
- **Sugerencia de corrección:** Normalizar y validar unicidad de `name`, exigir dígitos en `barcode` guardando el valor limpio sin espacios, y rechazar `e`/`E` en campos decimales.

---

### HAL-025 — El cobro (`/ventas/cobrar/`) no recalcula en vivo el Total, la Base imponible ni el IGV cuando la cajera escribe un Descuento
- **Severidad:** Media
- **Rol / persona:** Vendedora (Carmen)
- **Escenario:** C6
- **Pasos para reproducir:**
  1. Agregar productos al borrador por `S/ 13,00` e ir a `/ventas/cobrar/`.
  2. Ingresar `Descuento (S/): 3.00`.
  3. Mirar el panel derecho **Resumen de la venta** para saber cuánto efectivo pedirle al cliente.
- **Esperado:** Que la cajera vea el nuevo total a cobrar (`S/ 10,00`) antes de pedir el dinero y confirmar el cobro.
- **Real:** El panel derecho sigue diciendo `Total a cobrar: S/ 13,00` (estático), con una nota pequeña en el campo de descuento que dice: *"El total mostrado a la derecha es sin descuento; el recibo mostrará el total final."* Carmen tiene que restar mentalmente antes de cobrar.
- **Evidencia:** Texto en `GET /ventas/cobrar/`: `El total mostrado a la derecha es sin descuento; el recibo mostrará el total final. ... Total a cobrar S/ 13,00`.
- **Tipo:** Usabilidad en caja
- **HU / planificación relacionada:** `HU-VEN-03` (Post-Sprint, `AUDITORIA_USABILIDAD_05NOV2026.md` §14)
- **Sugerencia de corrección:** Añadir un pequeño cálculo en JavaScript en `sales_checkout.html` que actualice el total a cobrar y el vuelto estimado a medida que se escribe el descuento y el efectivo recibido.

---

### HAL-026 — Creación de Empleados (`/empleados/nuevo/`) acepta contraseñas triviales (`12345678`) y no ofrece confirmación ni forma de cambiar contraseñas después
- **Severidad:** Media
- **Rol / persona:** Administrador (Ana)
- **Escenario:** A3, A4
- **Pasos para reproducir:**
  1. En `/empleados/nuevo/`, crear un empleado con contraseña `12345678` (o `aaaaaaaa`): solo valida `min_length=8` y la acepta (`302`).
  2. Luego, si un empleado olvida su contraseña, entrar a `/empleados/<id>/editar/`: el formulario de edición solo tiene `Nombre completo`, `Correo de trabajo` y `Rol`. No existe ningún campo ni pantalla en todo el sistema para restablecer la contraseña de un empleado.
- **Esperado:** Que se apliquen los validadores de contraseña de Django (`validate_password`) y que el Administrador pueda restablecer la contraseña de un empleado si la olvida.
- **Real:** Contraseñas débiles de 8 caracteres son aceptadas y no existe función de cambio/reseteo de contraseña.
- **Evidencia:** `POST /empleados/nuevo/` con `password=12345678` → `302 /empleados/`; `GET /empleados/<id>/editar/` → campos `['csrfmiddlewaretoken', 'display_name', 'email', 'role']`.
- **Tipo:** Seguridad / Falta de funcionalidad
- **HU / planificación relacionada:** `HU-USR-02`, `HU-USR-03` (Sprints 2 y 3)
- **Sugerencia de corrección:** Invocar `validate_password` en el formulario de creación y añadir una opción de cambio de contraseña en la edición de empleados.

---

### HAL-027 — Sin bloqueo ni limitación de intentos fallidos de inicio de sesión (fuerza bruta ilimitada en `/`)
- **Severidad:** Media
- **Rol / persona:** Todos los roles
- **Escenario:** A1
- **Pasos para reproducir:**
  1. En `/`, enviar 7 veces seguidas una contraseña incorrecta para `admin.demo@pmv.invalid`.
  2. En el 8.º intento, enviar la contraseña correcta (`Admin1234!`).
- **Esperado:** Que tras 5–6 intentos fallidos consecutivos se bloquee temporalmente o se aplique un retardo (rate-limiting).
- **Real:** Los 7 intentos fallidos devuelven `200 OK` (`Correo o contraseña incorrectos` — correctamente no revela si el correo existe ni si está inactivo), e inmediatamente el 8.º intento entra sin ningún bloqueo (`302 -> /inicio/`).
- **Evidencia:** 7 `POST /` fallidos seguidos + 1 `POST /` exitoso → `302 /inicio/`.
- **Tipo:** Seguridad
- **HU / planificación relacionada:** No planificada
- **Sugerencia de corrección:** Implementar límite de intentos fallidos por IP/cuenta (ej. bloqueo temporal de 5 minutos tras 5 intentos fallidos).

---

### HAL-028 — El login (`/?next=...`) ignora el parámetro `next` y redirige siempre a `/inicio/`
- **Severidad:** Media
- **Rol / persona:** Administrador (Ana) y todos los roles
- **Escenario:** A2, C14
- **Pasos para reproducir:**
  1. Sin sesión iniciada, abrir directamente `http://127.0.0.1:8000/productos/nuevo/`.
  2. El sistema redirige a `/?next=/productos/nuevo/`.
  3. Iniciar sesión con las credenciales de Administrador en `/?next=/productos/nuevo/`.
- **Esperado:** Que tras iniciar sesión el sistema lleve a Ana directamente a `/productos/nuevo/`, que era la pantalla que intentaba abrir.
- **Real:** El login ignora `next` y redirige siempre a `/inicio/`.
- **Evidencia:** `GET /productos/nuevo/` (anónimo) → `302 /?next=/productos/nuevo/`; `POST /?next=/productos/nuevo/` → `302 /inicio/`.
- **Tipo:** Usabilidad
- **HU / planificación relacionada:** Acceso / Login
- **Sugerencia de corrección:** Respetar el parámetro `next` validado con `url_has_allowed_host_and_scheme` tras autenticar al usuario.

---

### HAL-030 — Las páginas 404 (`/hola/`, `/ventas/constancia/abc/`) se muestran en inglés crudo y sin botón para volver al sistema
- **Severidad:** Baja
- **Rol / persona:** Todos los roles
- **Escenario:** C9, Sección 6
- **Pasos para reproducir:**
  1. Abrir una ruta inexistente como `/hola/` o `/ventas/constancia/abc/`.
- **Esperado:** Una pantalla 404 en español con el diseño del sistema y un botón "Volver al inicio".
- **Real:** Página plana por defecto en inglés (`Not Found — The requested resource was not found on this server.`), callejón sin salida que obliga a usar el botón Atrás del navegador.
- **Evidencia:** `GET /hola/` → `404 Not Found — The requested resource was not found on this server.`.
- **Tipo:** Usabilidad / Textos
- **HU / planificación relacionada:** No planificada
- **Sugerencia de corrección:** Crear un template `404.html` en español con enlace a `/inicio/`.

---

### HAL-031 — Inconsistencia de estilos visuales (Bootstrap sin cargar en Empleados, Historial y Movimientos) y pérdida de formato al actualizar una línea del borrador con error
- **Severidad:** Baja
- **Rol / persona:** Todos los roles
- **Escenario:** A3, B6, C5, Sección 7
- **Pasos para reproducir:**
  1. Entrar a `/empleados/`, `/empleados/nuevo/`, `/ventas/historial/`, `/ventas/historial/turno/` o `/inventario/productos/<id>/movimientos/`: los templates usan clases de Bootstrap (`row justify-content-center`, `col-md-6`, `form-control`, `btn btn-primary`, `text-danger`), pero `base.html` solo carga `/static/identity/app.css` (que usa clases propias como `button button-primary`, `field`, `panel`), por lo que esos formularios y botones se ven sin el estilo del resto del sistema.
  2. Además, en `/ventas/` (C5), al actualizar una línea del borrador (`/ventas/lineas/<id>/`) con una cantidad inválida (`0`, `-3`, `abc` o `1000`), la vista redirige a `/ventas/` mostrando el mensaje en una alerta superior en vez de junto a la línea modificada. Si se pasa un UUID de línea inexistente (`POST /ventas/lineas/11111111-.../`), redirige silenciosamente (`302 -> /ventas/`) sin avisar que la línea no existe.
- **Esperado:** Diseño visual uniforme en todas las pantallas y mensajes contextuales claros.
- **Real:** Dos sistemas de clases CSS incompatibles mezclados en las plantillas.
- **Evidencia:** Inspección de clases en `/empleados/nuevo/`: `['class="row justify-content-center"', 'class="col-md-6"', 'class="form-control"', 'class="btn btn-primary"']` sin hoja de estilos de Bootstrap cargada.
- **Tipo:** Usabilidad / Consistencia visual
- **HU / planificación relacionada:** `HU-USR-01..04`, `HU-VEN-05a/b`, `HU-INV-06`
- **Sugerencia de corrección:** Unificar las clases CSS de todos los templates al sistema de diseño de `static/identity/app.css`.

---

### HAL-032 — Jerga técnica sin explicación para un almacenero o cajero que viene de usar cuadernos
- **Severidad:** Baja
- **Rol / persona:** Almacenero (Bruno) y Vendedora (Carmen)
- **Escenario:** B9, Cadena 7 (Sección 5)
- **Pasos para reproducir:**
  1. Recorrer las pantallas de Almacén, Caja y Ventas anotando los términos técnicos y las diferencias de vocabulario entre pantallas.
- **Esperado:** Términos cotidianos de bodega o breves ayudas en pantalla.
- **Real:**
  - **Stock físico vs. Stock vendible** (`/inventario/stock/`): no hay ningún tooltip ni nota en la página que explique por qué un producto tiene `Stock físico: 5` y `Stock vendible: 0` (que el vendible excluye lotes vencidos).
  - **Merma vs. Baja de inventario**: el menú lateral dice `Registrar merma`, el encabezado superior dice `Registrar merma`, pero el título `<title>` y el `<h1>` dicen `Baja de inventario` y el mensaje de éxito dice `Baja B-00000005 registrada correctamente`.
  - **Ajuste físico / Ajuste (positivo=entrada, negativo=faltante)**: no explica si debe escribir el conteo final que vio en el estante o la diferencia (`+5` / `-3`), lo que lleva fácilmente a que el usuario escriba `50` pensando que fija el stock en 50 cuando en realidad le suma `+50`.
  - **Correlativo**: usado en `/ventas/historial/` y en bajas sin explicar qué formato tiene (`V-00000001`).
  - **Base imponible**: mostrado en preparación de venta y cobro sin explicación.
  - **Constancia interna vs. Recibo**: en `/ventas/cobrar/` el texto de ayuda dice *"el recibo mostrará el total final"*, y más abajo *"registra la constancia interna"*.
  - **Formato numérico mixto (coma vs. punto)**: las tablas muestran `S/ 10,00` (con coma), pero en el cierre de caja exacto muestra `Exacto S/ 0.00` (con punto) y los errores de validación dicen `0.01` / `S/ 37.30` (con punto), mientras que escribir `10,50` en un formulario es rechazado con `"Introduzca un número."`.
- **Evidencia:** Textos verificados en `/inventario/stock/`, `/inventario/bajas/nueva/`, `/inventario/ajustes/nuevo/`, `/ventas/cobrar/` y `/caja/turnos/<id>/cerrado/`.
- **Tipo:** Usabilidad / Textos
- **HU / planificación relacionada:** Transversal
- **Sugerencia de corrección:** Añadir textos breves de ayuda en `stock_overview.html` (explicando "Stock vendible = existencias de lotes no vencidos") y en `adjustment_form.html` (aclarando que se ingresa la diferencia a sumar o restar).

---

### HAL-033 — En el Arqueo de Caja (`/caja/cerrar/`), una venta en preparación abandonada bloquea el cierre sin ofrecer un botón directo para descartarla desde ahí
- **Severidad:** Baja
- **Rol / persona:** Vendedora (Carmen)
- **Escenario:** C12
- **Pasos para reproducir:**
  1. Carmen deja un producto en su borrador de venta (`/ventas/`) porque el cliente se arrepintió y se fue.
  2. Al final de su jornada, Carmen va a **Cerrar turno** (`/caja/cerrar/`), cuenta sus billetes, escribe `230.00` y pulsa **Cerrar turno**.
- **Esperado:** Que pueda descartar el borrador pendiente con un clic desde la misma alerta o que en `/ventas/` exista un botón "Vaciar / Descartar venta en preparación".
- **Real:** El cierre es rechazado con el mensaje `"Hay una venta en preparación con productos. Descártala o cóbrala antes de cerrar el turno."`, pero no hay enlace a `/ventas/` en ese mensaje y en `/ventas/` tampoco existe un botón "Descartar venta": Carmen tiene que volver a `/ventas/` y pulsar **Quitar** producto por producto hasta dejar la lista vacía.
- **Evidencia:** `POST /caja/cerrar/` con borrador activo → `200 OK` (`Hay una venta en preparación con productos. Descártala o cóbrala antes de cerrar el turno.`).
- **Tipo:** Usabilidad
- **HU / planificación relacionada:** `HU-CAJA-02`, `HU-VEN-01b` (Sprint 1)
- **Sugerencia de corrección:** Agregar un botón "Descartar venta en preparación" en `/ventas/` y un enlace directo a `/ventas/` en el mensaje de bloqueo de `/caja/cerrar/`.

---

## 3. Matriz de escenarios

| ID | Persona / Sección | Descripción resumida | Resultado | Hallazgo(s) |
|---|---|---|---|---|
| **A1** | Ana (Admin) | Login: mayúsculas/espacios (OK), sin `@` (OK), vacía (OK), 6+ intentos fallidos seguidos, botón atrás tras `/salir/` (`no-store` OK) | **FALLA** | `HAL-027` (sin bloqueo tras 7 fallos) |
| **A2** | Ana (Admin) | Abrir `/productos/nuevo/` sin sesión (`302 /?next=...`) y loguearse | **FALLA** | `HAL-028` (ignora `next`, manda a `/inicio/`) |
| **A3** | Ana (Admin) | Crear empleado: vacíos, correo repetido/inactivo, contraseña débil (`1234` vs `12345678`), 300 chars, espacios, XSS escapado, rol manipulado | **FALLA** | `HAL-006`, `HAL-026`, `HAL-031` |
| **A4** | Ana (Admin) | Editar empleado: cambiar rol del propio Admin a Vendedor, desactivar único Admin (bloqueado OK), desactivar Vendedor con turno abierto | **FALLA** | `HAL-011`, `HAL-018`, `HAL-026` |
| **A5** | Ana (Admin) | Crear producto: precios raros (`0`, `-5`, `abc`, `10,50`, `1e5`, 15 dec), stock mín negativo, barcode letras/espacios, nombre duplicado, categoría inválida (`zzz`), doble envío | **FALLA** | `HAL-006`, `HAL-024` |
| **A6** | Ana (Admin) | Producto recién creado: aparece en Stock con 0 unidades; Vendedor lo busca y ve `"No se encontraron productos con existencias vendibles."` | **OK** | — |
| **A7** | Ana (Admin) | Desactivar producto que está dentro de una venta en preparación de un vendedor y luego intentar cobrar | **FALLA** | `HAL-012` (falla sin mensaje en `/ventas/cobrar/`) |
| **A8** | Ana (Admin) | Crear categoría repetida/vacía/con símbolos y tratar de usar categoría nueva al crear producto | **FALLA** | `HAL-023` (categorías nuevas no aparecen en el select) |
| **A9** | Ana (Admin) | Ajuste físico: delta 0, negativo excesivo, positivo enorme (`500`), lote UUID falso (`404`), lote no-UUID (`500`), motivo vacío | **FALLA** | `HAL-004`, `HAL-005`, `HAL-007`, `HAL-015` |
| **A10** | Ana (Admin) | Proveedor: RUC con 10, 11 y 12 dígitos, con letras, repetido; desactivar/reactivar; búsqueda con caracteres especiales (`%`, `'; --`, `<script>`) | **FALLA** | `HAL-022` (acepta RUC de 10 dígitos y con letras) |
| **A11** | Ana (Admin) | Resumen (`/inicio/`) comparado con Historial de ventas, Turnos y Stock tras una venta | **FALLA** | `HAL-001`, `HAL-008`, `HAL-013`, `HAL-016`, `HAL-017` |
| **B1** | Bruno (Almacén) | Buscar dónde registrar entrada de 50 unidades de un producto que ya tiene existencias | **FALLA** | `HAL-020` (no existe para Almacenero ni se explica) |
| **B2** | Bruno (Almacén) | Carga inicial: fechas ayer/hoy/50 años/`31/02/2027`, cantidades `0`/`-3`/`2.5`/`1e3`/enorme, costo `0`/6 dec, lote repetido `L1` vs `l1`, sin lotes, doble envío, producto ya cargado | **FALLA** | `HAL-005`, `HAL-019` |
| **B3** | Bruno (Almacén) | Merma: mayor al disponible, 0, motivo vacío, daño/robo sin detalle, lote agotado, lote vencido, `?lote=` falso (`404`) y no-UUID (`500`), doble envío rápido | **FALLA** | `HAL-004`, `HAL-015` (doble envío descuenta doble) |
| **B4** | Bruno (Almacén) | Probar Ajuste físico como Almacenero (no está en menú, pero sí hay botón en `/inventario/stock/` que lleva a `403`) | **FALLA** | `HAL-020`, `HAL-029` |
| **B5** | Bruno (Almacén) | Stock: sin lotes, bajo el mínimo, vence en 12 días, lote vencido con unidades, diferencia stock físico vs vendible | **FALLA** | `HAL-003`, `HAL-010`, `HAL-016`, `HAL-032` |
| **B6** | Bruno (Almacén) | Movimientos de un producto: ¿incluyen las ventas hechas por el Vendedor?, UUID inválido (`404`), producto sin movimientos | **FALLA** | `HAL-007`, `HAL-009` (no incluye ventas y altera carga inicial) |
| **B7** | Bruno (Almacén) | Proveedores como Almacenero: creación (`403`), búsqueda por nombre/RUC, lista vacía | **FALLA** | `HAL-021` (sin link en menú, pero muestra botones que dan 403) |
| **B8** | Bruno (Almacén) | Rutas `/productos/` (`200` con botones que dan `403`) y `/empleados/` (`403`) como Almacenero | **FALLA** | `HAL-021`, `HAL-029` |
| **B9** | Bruno (Almacén) | Vocabulario comprensible para quien viene de cuadernos | **FALLA** | `HAL-032` |
| **C1** | Carmen (Ventas) | Entrar a `/ventas/` sin abrir turno: muestra mensaje claro y botón `"Ir a apertura de caja"` | **OK** | — |
| **C2** | Carmen (Ventas) | Abrir turno: efectivo vacío, negativo, `abc`, enorme, 3 decimales; abrir 2.º turno; caja ocupada por otro vendedor | **OK** | Validaciones claras en `/caja/abrir/` |
| **C3** | Carmen (Ventas) | Buscar producto: vacío, espacios, mayús/minús, parcial, código de barras, `%`, `'`, `;--`, `<script>`, sin stock, desactivado, lote vencido | **OK** | Escapa XSS, ignora inactivos/vencidos/sin stock |
| **C4** | Carmen (Ventas) | Agregar al borrador: 0, negativa, decimal, `abc`, mayor al stock vendible, mismo producto dos veces (suma OK), `99999999999` | **OK** | Suma cantidades y valida tope contra stock vendible |
| **C5** | Carmen (Ventas) | Modificar y quitar líneas: cantidad > stock, 0, negativa, quitar última línea (oculta botón Cobrar OK), línea de otro vendedor (`404`/ignorado) | **FALLA** | `HAL-031` (UUID falso redirige sin aviso) |
| **C6** | Carmen (Ventas) | Cobrar: efectivo menor, exacto, 3 dec, `0`; descuento >= subtotal, negativo, decimales, `abc`; descuento válido + IGV/base/vuelto; doble clic y F5 | **FALLA** | `HAL-025` (no recalcula total con descuento antes de cobrar; idempotencia sí evita duplicar venta) |
| **C7** | Carmen (Ventas) | Cobrar sin productos / ir directo a `/ventas/cobrar/` con borrador vacío (`302 -> /ventas/` con aviso `"No tienes una venta en preparación."`) | **OK** | — |
| **C8** | Carmen (Ventas) | Dos pestañas cobrando la misma venta (2.ª redirige sin duplicar OK); merma concurrente deja stock insuficiente (muestra error claro OK); Admin desactiva producto (falla muda) | **FALLA** | `HAL-012` (cuando el producto fue desactivado por Admin) |
| **C9** | Carmen (Ventas) | Recibo: abrir `/ventas/constancia/<id>/` de otro vendedor (`404` OK); reabrir tras cerrar turno (`200` OK); imprimir (`window.print()` OK) | **FALLA** | `HAL-008`, `HAL-013`, `HAL-014` |
| **C10** | Carmen (Ventas) | Anular o corregir una venta ya cobrada (no existe ninguna función en el sistema) | **FALLA** | Falta de funcionalidad (documentado en Sección 5) |
| **C11** | Carmen (Ventas) | Resumen del día: "Mis ventas del turno" (`/ventas/historial/turno/`) vs lo cobrado | **FALLA** | `HAL-008` (correlativo y vuelto en blanco; no muestra suma total del turno) |
| **C12** | Carmen (Ventas) | Cerrar turno: con borrador pendiente, contado vacío/negativo/distinto al esperado (muestra Faltante/Exacto), cerrar 2 veces, vender tras cerrar | **FALLA** | `HAL-017`, `HAL-033` |
| **C13** | Carmen (Ventas) | Cerrar sesión con borrador pendiente: `/salir/` avisa `"La venta en preparación se descartará."` y al volver el borrador fue descartado | **OK** | — |
| **C14** | Carmen (Ventas) | Sesión: copiar URL interna sin sesión (`302 /?next=...`), botón atrás tras `/salir/` (`Cache-Control: no-store` OK) | **FALLA** | `HAL-028` (no redirige a `next` tras loguearse) |
| **S5-1** | Coherencia 1 | Producto de punta a punta: Admin crea → Almacenero carga → Vendedor vende → Movimientos, Stock, Resumen e Historial | **FALLA** | `HAL-007`, `HAL-008`, `HAL-009`, `HAL-013` |
| **S5-2** | Coherencia 2 | FEFO: producto con 2 lotes (`A1` vence en 12 días con 10 u., `A2` vence en 300 días con 20 u.), vender 15 unidades → `A1=0, A2=15` | **OK** | Descuenta exactamente por orden de vencimiento (FEFO) |
| **S5-3** | Coherencia 3 | Dinero: apertura S/ 100 + ventas (con descuento) = S/ 193,90 esperado vs acta de cierre vs Historial de turnos Admin | **FALLA** | `HAL-017` (el cálculo es exacto en el acta, pero `/caja/turnos/` no muestra esperado, contado ni diferencia) |
| **S5-4** | Coherencia 4 | Desactivaciones en cascada: desactivar vendedor con turno abierto, producto en borrador, proveedor en uso | **FALLA** | `HAL-012`, `HAL-018` |
| **S5-5** | Coherencia 5 | Menú vs permisos en todos los roles (incluyendo tarjetas/botones de pantallas internas) | **FALLA** | `HAL-010`, `HAL-013`, `HAL-014`, `HAL-020`, `HAL-021` |
| **S5-6** | Coherencia 6 | Alertas vs realidad: modificar stock y vencimientos y comparar `/inicio/` vs `/inventario/stock/` vs `/productos/vencimientos/` | **FALLA** | `HAL-003`, `HAL-010`, `HAL-016` |
| **S5-7** | Coherencia 7 | Nombres y textos: consistencia de marca, términos y formato de moneda | **FALLA** | `HAL-029`, `HAL-032` |
| **S6-1** | Seguridad 1 | Manipulación de UUIDs en URLs (de otro usuario, UUID falso, texto no-UUID `abc`/`zzz`) | **FALLA** | `HAL-004` (`?lote=zzz` da 500 en bajas y ajustes) |
| **S6-2** | Seguridad 2 | Envío POST sin token CSRF (`enforce_csrf_checks=True`) → `403 Forbidden` limpio | **OK** | — |
| **S6-3** | Seguridad 3 | Peticiones GET en endpoints solo-POST (`.../estado/`, `.../quitar/`, `.../disponibilidad/`, `/ventas/lineas/<id>/`) → `405 Method Not Allowed` | **OK** | — |
| **S6-4** | Seguridad 4 | Parámetros extraños en GET (`?query=<script>`, `?fecha=hoy`, `?fecha=2026-13-45`, `?correlativo=%`, `?dias=abc`, `?dias=`) | **FALLA** | `HAL-001`, `HAL-002`, `HAL-003` (múltiples errores 500) |
| **S6-5** | Seguridad 5 | Rutas inexistentes (`/hola/`) | **FALLA** | `HAL-030` (404 en inglés sin retorno) |
| **S6-6** | Seguridad 6 | Manipulación de roles: Vendedor abriendo rutas de Admin y de Pagos (`/pagos/gerencia/`) → `403` | **OK** | Bloqueado con 403 |

---

## 4. Coherencia entre roles (sección 5 del prompt)

### Cadena 1 — Producto de punta a punta
- **Ejecución y números comparados:**
  1. **Admin (Ana)** creó `Prod Test 15` (`barcode: 9990000015`, `sale_price: S/ 5,00`, `minimum_stock: 10`). En `/inventario/stock/` apareció con `Stock físico: 0`, `Stock vendible: 0`.
  2. **Almacenero (Bruno)** registró carga inicial en `/inventario/carga-inicial/` con 2 lotes: `A1` (`10 unid.`, vence `17/11/2026`) y `A2` (`20 unid.`, vence `01/09/2027`). Stock total = **30 unidades**.
  3. **Vendedora (Carmen)** vendió **15 unidades** en la venta `V-00000003` (`S/ 75,00`) y luego **2 unidades** en `V-00000005` (`S/ 10,00`).
  4. **Almacenero (Bruno)** registró mermas sobre `Lote A2`: `-3`, `-3`, `-5`, `-1` (total mermas = **-12 unidades**).
  5. **Admin (Ana)** registró un ajuste físico sobre `Lote A2` de **+2 unidades**.
  6. **Ecuación real en Stock (`/inventario/stock/`):**
     $$\text{Stock final} = 30\text{ (inicial)} - 17\text{ (vendido)} - 12\text{ (mermas)} + 2\text{ (ajuste)} = 3\text{ unidades}$$
     En `/inventario/stock/` aparece efectivamente `Stock físico: 3`, `Stock vendible: 3`.
- **Inconsistencias detectadas en la cadena:**
  - En `/inventario/productos/<id>/movimientos/` **NO aparecen las 2 ventas (`-15` y `-2`)** (`HAL-009`).
  - El ajuste positivo de `+2` **modificó retroactivamente la fila `Carga inicial — Lote A2` de `+20` a `+22`** (`HAL-007`), por lo que la tabla de movimientos muestra `+10 + 22 - 3 - 3 - 5 - 1 + 2 = 22` mientras el encabezado dice `Stock físico actual: 3 unid.`.
  - En `/ventas/historial/` el Administrador ve la fila de la venta pero las columnas `Correlativo` y `Vuelto` están en blanco (`HAL-008`), el filtro por correlativo da `500` (`HAL-001`) y si intenta abrir la constancia recibe `403` (`HAL-013`).

### Cadena 2 — FEFO (First Expired, First Out)
- **Ejecución y números comparados:**
  - `Prod Test 15` tenía `Lote A1` con **10 unidades** (vencimiento `17/11/2026`) y `Lote A2` con **20 unidades** (vencimiento `01/09/2027`).
  - Se vendieron **15 unidades** en una sola línea de venta (`V-00000003`).
  - **Resultado en BD y en pantallas:** `Lote A1` quedó en **0 unidades** y `Lote A2` quedó en **15 unidades**. El descuento FEFO entre múltiples lotes funciona de forma exacta.

### Cadena 3 — Dinero (Apertura, Ventas con descuento, Arqueo y Cierre)
- **Ejecución y números comparados:**
  - **Turno 1:** Abierto con `S/ 200,00`. Ventas del turno: `V-00000001` (`S/ 10,00`, desc. `S/ 3,00`) + `V-00000002` (`S/ 32,30`, desc. `S/ 5,00`).
    $$\text{Efectivo esperado} = 200,00 + 10,00 + 32,30 = \text{S/ } 242,30$$
    Al declarar `Monto contado: S/ 230,00`, el Acta de cierre (`/caja/turnos/<id>/cerrado/`) mostró: `Monto inicial: S/ 200,00`, `Monto esperado: S/ 242,30`, `Monto contado: S/ 230,00`, `Diferencia: Faltante S/ -12,30`.
  - **Turno 2:** Abierto con `S/ 100,00`. Ventas del turno: `V-00000003` (`S/ 75,00`, sin desc.) + `V-00000004` (`S/ 8,90`, desc. `S/ 1,50`) + `V-00000005` (`S/ 10,00`, sin desc.).
    $$\text{Efectivo esperado} = 100,00 + 75,00 + 8,90 + 10,00 = \text{S/ } 193,90$$
    Al declarar `Monto contado: S/ 193,90`, el Acta de cierre mostró `Diferencia: Exacto S/ 0.00`.
  - **Resumen del Admin (`/inicio/`):** Mostró `Ventas de hoy: 5`, `Total vendido hoy: S/ 136,20` (`10,00 + 32,30 + 75,00 + 8,90 + 10,00 = 136,20`), `Descuentos otorgados hoy: S/ 9,50` (`3,00 + 5,00 + 1,50 = 9,50`), `Turnos de caja abiertos: 0`.
- **Inconsistencias detectadas en la cadena:**
  - En `/caja/turnos/` (tanto para Admin como para Vendedor) **no se muestran** los montos esperados (`242,30` / `193,90`), ni los contados (`230,00` / `193,90`), ni las diferencias (`-12,30` / `0,00`), ni hay enlace para reabrir el Acta de cierre (`HAL-017`).

### Cadena 4 — Desactivaciones en cascada
- **Vendedor desactivado en pleno turno con borrador activo:** Su sesión se invalida en el próximo clic (`302 /?next=/ventas/`), pero su turno en `CAJA-01` **queda abierto y huérfano**, bloqueando la apertura de caja para cualquier otro vendedor (`HAL-018`). Al reactivarlo, conserva su turno y su borrador intactos.
- **Producto deshabilitado mientras está en el borrador de un vendedor:** El vendedor sigue viendo el producto en su borrador y al pulsar **Confirmar cobro** en `/ventas/cobrar/`, el cobro se rechaza **sin mostrar ningún mensaje de error en pantalla** (`HAL-012`).
- **Proveedor desactivado:** Cambia de `Activo` a `Inactivo` en `/inventario/proveedores/` sin afectar productos ni lotes porque los lotes no están vinculados a ningún proveedor en el modelo de datos (ver Sección 5).

### Cadena 5 — Menú vs permisos (todos los roles)
- **Administrador (`ADMIN`):** Todos los enlaces de su menú lateral devuelven `200 OK`. Sin embargo:
  - En `/inventario/stock/` ve el botón `+ Registrar existencias iniciales` (`/inventario/carga-inicial/`) que le devuelve `403` (`HAL-020`).
  - En `/ventas/historial/` cada venta enlaza a `/ventas/constancia/<id>/`, que le devuelve `403` (`HAL-013`).
  - `/productos/vencimientos/` existe y el Admin tiene permiso (`200`), pero **no está en su menú lateral** (`HAL-010`).
- **Almacenero (`ALMACENERO`):** Todos los enlaces de su menú lateral devuelven `200 OK`. Sin embargo:
  - En `/inventario/stock/` ve el botón `Ajuste físico` (`/inventario/ajustes/nuevo/`) que le devuelve `403` (`HAL-020`).
  - Tiene permiso `200 OK` en `/productos/`, `/productos/vencimientos/` y `/inventario/proveedores/`, pero **ninguna de las tres está en su menú lateral**, y dentro de `/productos/` y `/inventario/proveedores/` ve botones de crear/editar/desactivar que le dan `403` (`HAL-010`, `HAL-021`).
- **Vendedor (`VENDEDOR`):** Todos los enlaces de su menú lateral devuelven `200 OK`. Sin embargo:
  - No tiene enlace en su menú a `/caja/turnos/` ni a `/ventas/historial/`, pero puede abrir ambas por URL (`200 OK`) y ver los turnos y ventas de otros vendedores (`HAL-014`).
## 5. Funciones esperadas por un usuario nuevo que NO existen

Lista honesta de huecos funcionales que una persona real (administradora, almacenero o cajera) busca en su primer día y que **no existen en el sistema**:

1. **Anular, devolver o corregir una venta ya cobrada (Escenario C10):** Si Carmen se equivoca al cobrar (ej. digitó 50 latas en vez de 5, o el cliente devuelve un producto un minuto después), **no existe botón ni flujo de anulación, nota de crédito ni devolución** en ningún rol (ni Vendedor ni Admin). La única forma artificial de cuadrar el stock es que el Admin haga un ajuste físico manual, pero el dinero de la caja y el total vendido del día quedan inflados permanentemente sin posibilidad de corrección.
2. **Registrar entradas periódicas de mercadería por el Almacenero (Escenario B1):** "Existencias iniciales" (`/inventario/carga-inicial/`) solo permite cargar cada producto **una única vez en su historia**. Cuando llega el segundo pedido de un proveedor con un lote nuevo y nueva fecha de vencimiento, **no existe ninguna pantalla de "Recepción de mercadería / Entrada de nuevo lote"**. Incluso el "Ajuste físico" del Admin solo permite sumar o restar unidades a un lote que ya existía, pero **tampoco permite crear un lote nuevo con nueva fecha de vencimiento y nuevo costo** para un producto que ya tuvo su carga inicial (a pesar de que `CONTROL_SPRINTS.md` lista `HU-INV-01b: Recalcular costo promedio en entradas posteriores`).
3. **Vincular entradas de mercadería o productos con un Proveedor (Escenario A10 / B7):** Existe un catálogo de Proveedores (`/inventario/proveedores/`), pero el modelo `Supplier` está completamente desconectado del resto del sistema: ni los productos, ni las cargas iniciales, ni los lotes tienen campo de proveedor. Registrar proveedores no sirve para ninguna operación del minimarket.
4. **Restablecer o cambiar la contraseña de un empleado (Escenario A3 / A4):** Si un trabajador olvida su contraseña o quiere cambiar la contraseña inicial que le puso el Admin, no existe función de "Cambiar contraseña" ni en la edición de empleados (`/empleados/<id>/editar/`) ni en el perfil del usuario.
5. **Botón para vaciar/descartar una venta en preparación completa (Escenario C5 / C12):** Si un cliente deja 10 productos en el mostrador y se va sin pagar, la cajera tiene que pulsar "Quitar" fila por fila 10 veces para poder atender al siguiente cliente o para poder cerrar su turno.
6. **Total del turno en "Mis ventas del turno" (`/ventas/historial/turno/`, Escenario C11):** La pantalla lista las filas de ventas del turno actual, pero no muestra la suma total vendida en el turno ni el efectivo esperado en caja hasta que la vendedora entra a cerrar el turno.
7. **Editar datos de un proveedor (`/inventario/proveedores/`, Escenario A10):** Si el Admin se equivoca en una letra del nombre o en el teléfono de un proveedor, solo puede desactivarlo; no existe pantalla de edición de proveedor.

---

## 6. Calificación de usabilidad 1–10 por rol, con justificación

| Rol | Calificación (1–10) | Justificación detallada |
|---|---|---|
| **Administrador (Ana)** | **5.5 / 10** | **Puntos a favor:** Menú lateral organizado por secciones, panel de resumen general en `/inicio/`, creación y edición básica de productos y empleados funcional. **Puntos en contra:** Puede cambiar su propio rol y dejar el sistema sin ningún administrador (`HAL-011`); el filtro por correlativo en Historial de ventas lanza error 500 (`HAL-001`) y el de fecha inválida también lanza 500 (`HAL-002`); las columnas Correlativo y Vuelto en Historial de ventas están en blanco (`HAL-008`) y al abrir una constancia recibe 403 (`HAL-013`); en Historial de turnos no puede ver si hubo faltante o sobrante (`HAL-017`); puede crear categorías que luego no aparecen al registrar productos (`HAL-023`); el filtro de vencimientos no está en el menú, oculta el número de lote (`HAL-010`) y da error 500 si se envía vacío (`HAL-003`). |
| **Almacenero (Bruno)** | **5.0 / 10** | **Puntos a favor:** Vista unificada de stock y alertas (`/inventario/stock/`) y formulario de merma que exige motivo y detalle para daño o robo. **Puntos en contra:** No tiene ninguna forma de registrar la llegada de un nuevo lote de un producto que ya tuvo carga inicial (`HAL-020`); el botón "Ajuste físico" aparece en su pantalla de stock pero al pulsarlo le da 403 (`HAL-020`); el historial de movimientos de un producto **no muestra las ventas** (`HAL-009`) y los ajustes positivos alteran retroactivamente la cantidad de la carga inicial (`HAL-007`), por lo que los números nunca le cuadran con su cuaderno; el doble clic en merma descuenta el stock dos veces (`HAL-015`); y los lotes vencidos aparecen duplicados como "próximos a vencer" (`HAL-016`). |
| **Vendedora (Carmen)** | **6.5 / 10** | **Puntos a favor:** Flujo de apertura de caja, búsqueda de productos, validación de stock vendible, descuento por FEFO, prevención de doble cobro por `idempotency_key` y arqueo de cierre funcionan con solidez en el camino feliz. **Puntos en contra:** Si el Admin deshabilita un producto mientras está en el borrador, la pantalla de cobro falla en silencio sin decirle por qué no puede cobrar (`HAL-012`); al aplicar un descuento no ve el nuevo total a cobrar hasta después de emitir el recibo (`HAL-025`); en "Mis ventas del turno" las columnas Correlativo y Vuelto salen vacías (`HAL-008`); y no tiene forma de anular una venta equivocada ni de vaciar un borrador con un solo clic (`HAL-033`). |

---

## 7. Trazabilidad

### 7.1 Tabla `HAL-xxx` ↔ `HU` ↔ Archivo / URL

| Hallazgo | Severidad | HU relacionada | Archivo / Vista / Template involucrado | Contraste con `CONTROL_SPRINTS.md` / `AUDITORIA_USABILIDAD_05NOV2026.md` |
|---|---|---|---|---|
| **HAL-001** | Crítica | `HU-VEN-05b` (S2) | `sales/views.py::sales_history` (`/ventas/historial/`) | Declarada ✅ en Sprint 2, pero filtrar por correlativo lanza `500 FieldError`. |
| **HAL-002** | Crítica | `HU-VEN-05b` (S2) | `sales/views.py::sales_history` (`/ventas/historial/`) | Declarada ✅ en Sprint 2, pero una fecha inválida en GET lanza `500 ValidationError`. |
| **HAL-003** | Crítica | `HU-PROD-06` (S2) | `catalog/views.py::product_expirations` (`/productos/vencimientos/`) | Declarada ✅ en Sprint 2, pero pulsar "Filtrar" con `dias` vacío, texto o número grande lanza `500`. |
| **HAL-004** | Crítica | `HU-INV-02`, `HU-INV-03` (S3) | `inventory/views.py` (`/inventario/bajas/nueva/`, `/inventario/ajustes/nuevo/`) | Declaradas ✅ en Sprint 3, pero `?lote=zzz` no-UUID lanza `500 ValidationError`. |
| **HAL-005** | Crítica | `HU-INV-01` (S1), `HU-INV-03` (S3) | `inventory/services.py::register_physical_adjustment`, `inventory/forms.py` | Sin `max_value`; números grandes provocan `500 OverflowError` en SQLite. |
| **HAL-006** | Crítica | `HU-PROD-02`, `HU-USR-02/03` | `catalog/forms.py`, `identity/forms.py` (`/productos/nuevo/`, `/empleados/nuevo/`) | Expone `“zzz” no es un UUID válido` y códigos `ADMIN`/`ALMACENERO`/`VENDEDOR`. |
| **HAL-007** | Alta | `HU-INV-03` (S3), `HU-INV-06` (Post) | `inventory/services.py::register_physical_adjustment`, `inventory/views.py::product_movements` | Contradice `AUDITORIA` §13 (`HU-INV-06`): el ajuste positivo altera `initial_quantity` y reescribe la carga inicial. |
| **HAL-008** | Alta | `HU-VEN-05a`, `HU-VEN-05b` (S2) | `sales/templates/sales/sales_shift_history.html`, `sales_history.html` | Declaradas ✅ en Sprint 2 y `AUDITORIA` §10 (`C2-03`), pero `Correlativo` y `Vuelto` se renderizan vacíos. |
| **HAL-009** | Alta | `HU-INV-06` (Post) | `inventory/views.py::product_movements` (`/inventario/productos/<id>/movimientos/`) | Contradice `AUDITORIA` §13: el historial de movimientos omite todas las ventas y no cuadra con el stock actual. |
| **HAL-010** | Alta | `HU-PROD-06` (S2) | `catalog/templates/catalog/product_expirations.html`, `identity/templates/identity/base.html` | `AUDITORIA` §9 ya advertía que no tenía link en el menú; sigue sin link y además muestra `—` en el número de lote. |
| **HAL-011** | Alta | `HU-USR-03` (S3) | `identity/views.py::employee_edit` (`/empleados/<id>/editar/`) | Declarada ✅ en Sprint 3, pero permite que el único Admin se degrade a Vendedor y deje el sistema acéfalo. |
| **HAL-012** | Alta | `HU-PROD-05` (S2), `HU-VEN-01c` (S1) | `sales/views.py::sales_checkout`, `sales/templates/sales/sales_checkout.html` | Si se desactiva un producto que está en un borrador, `/ventas/cobrar/` falla sin mostrar ningún mensaje de error. |
| **HAL-013** | Alta | `HU-VEN-02a` (S1), `HU-VEN-05b` (S2) | `sales/views.py::sales_receipt` (`/ventas/constancia/<id>/`) | `/ventas/historial/` enlaza a la constancia, pero el Admin recibe `403` al abrirla. |
| **HAL-014** | Alta | `HU-VEN-05a`, `HU-VEN-05b` (S2) | `sales/views.py::sales_history` (`/ventas/historial/`) | Un vendedor puede ver por URL las ventas de todos los demás vendedores en `/ventas/historial/`. |
| **HAL-015** | Alta | `HU-INV-02`, `HU-INV-03` (S3) | `inventory/views.py` (`/inventario/bajas/nueva/`, `/inventario/ajustes/nuevo/`) | Carecen de `idempotency_key`; el doble envío descuenta o ajusta dos veces. |
| **HAL-016** | Alta | `HU-INV-04`, `HU-INV-05`, `HU-REP-01` | `inventory/views.py::stock_overview`, `identity/views.py::_admin_summary` | Contradice `AUDITORIA` §13–14: lotes vencidos se duplican como "próximos a vencer" y contadores de `/inicio/` vs `/inventario/stock/` difieren. |
| **HAL-017** | Alta | `HU-CAJA-02` (S1), `HU-CAJA-05` (S2) | `cash/templates/cash/cash_shift_history.html` (`/caja/turnos/`) | Declarada ✅ en Sprint 2, pero `/caja/turnos/` no muestra monto esperado, contado ni diferencia de cierre. |
| **HAL-018** | Media | `HU-USR-04` (S3), `HU-CAJA-01` (S1) | `identity/views.py::employee_toggle_active` (`/empleados/<id>/estado/`) | Desactivar a un vendedor con turno abierto deja `CAJA-01` bloqueada para todos los demás vendedores. |
| **HAL-019** | Media | `HU-INV-01` (S1) | `inventory/views.py`, `inventory/forms.py` (`/inventario/carga-inicial/`) | Mensaje confuso cuando el producto ya tiene carga inicial o falla la validación de lotes. |
| **HAL-020** | Media | `HU-INV-01`, `HU-INV-03`, `HU-INV-04` | `inventory/templates/inventory/stock_overview.html` (`/inventario/stock/`) | Muestra botones sin filtrar por rol (`Ajuste físico` al Almacenero y `Existencias iniciales` al Admin) que llevan a `403`. |
| **HAL-021** | Media | `HU-PROV-01` (S3), `HU-PROD-01` (S2) | `catalog/templates/catalog/product_list.html`, `inventory/templates/inventory/supplier_list.html` | El Almacenero accede por URL y ve botones de mutación (`Editar`, `Deshabilitar`, `+ Nuevo proveedor`) que dan `403`. |
| **HAL-022** | Media | `HU-PROV-02` (S3) | `inventory/models.py::Supplier`, `inventory/forms.py` (`/inventario/proveedores/nuevo/`) | Declarada ✅ en Sprint 3, pero acepta RUCs de 10 dígitos o con letras (`2012345678A`). |
| **HAL-023** | Media | `HU-CAT-01`, `HU-CAT-02` (S2) | `catalog/views.py`, `catalog/forms.py` (`/productos/categorias/nueva/`) | Permite crear categorías nuevas que nunca aparecen al registrar productos por la restricción de R1, sin explicarlo. |
| **HAL-024** | Media | `HU-PROD-02` (S1) | `catalog/models.py::Product`, `catalog/forms.py` (`/productos/nuevo/`) | Permite nombres duplicados con distinta mayúscula, códigos de barras con letras/espacios y precios `1e5`. |
| **HAL-025** | Media | `HU-VEN-03` (Post) | `sales/templates/sales/sales_checkout.html` (`/ventas/cobrar/`) | El resumen derecho no actualiza el total a cobrar al escribir un descuento. |
| **HAL-026** | Media | `HU-USR-02`, `HU-USR-03` (S2–S3) | `identity/forms.py`, `identity/views.py` (`/empleados/nuevo/`, `/empleados/<id>/editar/`) | Acepta contraseñas débiles (`12345678`) y no permite cambiar/restablecer contraseñas en edición. |
| **HAL-027** | Media | No planificada | `identity/views.py` (`/`) | Sin bloqueo ni rate-limiting tras múltiples intentos fallidos de login. |
| **HAL-028** | Media | Acceso / Login | `identity/views.py` (`/?next=...`) | El login ignora el parámetro `next` y redirige siempre a `/inicio/`. |
| **HAL-030** | Baja | No planificada | Manejador 404 por defecto (`/hola/`) | Respuesta 404 plana en inglés sin enlace para volver al inicio. |
| **HAL-031** | Baja | `HU-USR-01..04`, `HU-VEN-05a/b` | Templates con clases Bootstrap sin CSS de Bootstrap cargado | Inconsistencia visual entre pantallas de empleados/historial y el resto del sistema. |
| **HAL-032** | Baja | Transversal | Múltiples templates | Términos técnicos (stock vendible, ajuste físico, correlativo, base imponible) sin ayuda contextual y mezcla coma/punto decimal. |
| **HAL-033** | Baja | `HU-CAJA-02`, `HU-VEN-01b` (S1) | `cash/templates/cash/cash_close.html`, `sales/templates/sales/sales_draft.html` | Falta botón para descartar el borrador completo cuando bloquea el cierre de turno. |

### 7.2 Contradicciones principales entre la documentación/planificación y la realidad verificada

1. **`CONTROL_SPRINTS.md` declara `HU-INV-01b (Recalcular costo promedio en entradas posteriores)` como `✅ Completada` en el Sprint 3:** En la interfaz real del sistema **no existe ninguna pantalla para registrar entradas posteriores de lotes** (la carga inicial bloquea cualquier producto que ya tenga un lote, y el ajuste físico solo suma/resta unidades a un lote existente sin pedir costo unitario).
2. **`CONTROL_SPRINTS.md` declara `HU-VEN-05a` y `HU-VEN-05b` (Historial de ventas del turno y completo) como `✅ Completadas` en el Sprint 2:** En realidad, las tablas muestran en blanco el correlativo y el vuelto (`HAL-008`), el filtro por correlativo rompe con error 500 (`HAL-001`), el filtro por fecha inválida rompe con error 500 (`HAL-002`) y el Administrador recibe 403 al intentar abrir cualquier constancia desde ese historial (`HAL-013`).
3. **`AUDITORIA_USABILIDAD_05NOV2026.md` §13 declara `HUECO-03 / HU-INV-06 (Historial de movimientos por producto)` cerrado:** En realidad, la vista `/inventario/productos/<id>/movimientos/` no incluye las ventas (`HAL-009`) y los ajustes físicos positivos sobrescriben la cantidad de la carga inicial (`HAL-007`), haciendo que el historial no explique cómo se llegó al stock actual.

---

## 8. Resolución y Trazabilidad de Correcciones (05/11/2026 — Ronda 5)

Todos los hallazgos de código, validación, permisos, coherencia entre roles y usabilidad detectados en esta sesión exploratoria fueron corregidos y verificados con la suite automatizada de pruebas (`163 tests, OK, exit 0`).

| Hallazgo | Severidad | Estado | Archivos modificados | Detalle de la corrección aplicada |
|---|---|---|---|---|
| **HAL-001** | Crítica | ✅ Corregido | `sales/views.py`, `sales/tests.py` | Cambiado `correlativo__icontains` por `correlative__icontains` en `sales_history`. |
| **HAL-002** | Crítica | ✅ Corregido | `sales/views.py`, `sales/tests.py` | Validación previa con `parse_date(fecha)` en `sales_history`; si es inválida muestra alerta amigable sin lanzar `500`. |
| **HAL-003** | Crítica | ✅ Corregido | `catalog/views.py`, `catalog/tests.py` | Validación de `dias` en `product_expirations` (entero entre `1` y `3650`, fallback a `30` con aviso) evitando `ValueError` y `OverflowError`. |
| **HAL-004** | Crítica | ✅ Corregido | `inventory/views.py`, `inventory/tests.py` | Helper `_get_lot_or_404` valida formato UUID antes de consultar `Lot`, devolviendo `404` limpio en lugar de `500 ValidationError`. |
| **HAL-005** | Crítica | ✅ Corregido | `inventory/forms.py`, `inventory/services.py`, `catalog/forms.py` | Límites `max_value=999999` / `min_value=-999999` en cantidades de lotes, mermas, ajustes físicos y stock mínimo para evitar `OverflowError` en SQLite. |
| **HAL-006** | Crítica | ✅ Corregido | `catalog/forms.py`, `identity/forms.py` | Mensajes en español claro en `category`, `role` y `password`; `RoleChoiceField` muestra nombres legibles (`Administrador`, `Almacenero`, `Vendedor`). |
| **HAL-007** | Alta | ✅ Corregido | `inventory/views.py`, `inventory/tests.py` | `product_movements` calcula la carga inicial original restando los ajustes positivos posteriores y muestra el nombre del responsable real en vez de `"Sistema"`. |
| **HAL-008** | Alta | ✅ Corregido | `sales/templates/sales/sales_history.html`, `sales_shift_history.html`, `sales/views.py` | Corregidos atributos de plantilla a `{{ sale.correlative }}` y `{{ sale.change_given }}`; agregado total vendido del turno (`shift_total`). |
| **HAL-009** | Alta | ✅ Corregido | `inventory/views.py`, `inventory/templates/inventory/product_movements.html` | Incluidas las ventas (`SaleLine`) en el historial de movimientos del producto con correlativo, cantidad `-N` y vendedor responsable. |
| **HAL-010** | Alta | ✅ Corregido | `catalog/templates/catalog/product_expirations.html`, `identity/templates/identity/base.html` | Corregido `{{ lot.number_normalized|default:lot.number }}` y agregado enlace `Vencimientos de lotes` en el menú lateral de Admin y Almacenero. |
| **HAL-011** | Alta | ✅ Corregido | `identity/services.py`, `identity/tests.py` | `update_employee` impide que un Administrador cambie el rol de su propia cuenta (`"No puedes cambiar el rol de tu propia cuenta."`). |
| **HAL-012** | Alta | ✅ Corregido | `sales/services.py`, `sales/views.py`, `sales/templates/sales/sales_checkout.html` | `checkout_sale` verifica que todos los productos del borrador sigan activos, `sales_checkout` autogenera `idempotency_key` si falta y muestra errores de `discount_amount`. |
| **HAL-013** | Alta | ✅ Corregido | `sales/views.py` | `sales_receipt` autoriza a `ADMIN` y `SELLER` (manteniendo restricción `seller=request.user` solo para `SELLER`). |
| **HAL-014** | Alta | ✅ Corregido | `sales/views.py`, `cash/views.py` | `sales_history` y `cash_shift_history` filtran por `seller=request.user` cuando el usuario autenticado es `VENDEDOR`. |
| **HAL-015** | Alta | ✅ Corregido | `inventory/forms.py`, `inventory/views.py`, `writeoff_form.html`, `adjustment_form.html` | Añadido `idempotency_key` oculto y control en sesión (`_consume_inventory_idempotency_key`) para evitar doble descuento en mermas y ajustes. |
| **HAL-016** | Alta | ✅ Corregido | `inventory/views.py`, `identity/views.py`, `stock_overview.html` | Unificado criterio entre `/inicio/` y `/inventario/stock/`: `expiring_lots` excluye ya vencidos (`expiration_date__gt=today`) y `low_stock` evalúa productos activos con `sellable_stock < minimum_stock` o `sellable_stock == 0`. |
| **HAL-017** | Alta | ✅ Corregido | `cash/views.py`, `cash/templates/cash/cash_shift_history.html` | Añadidas columnas `Monto esperado`, `Monto contado`, `Diferencia` y botón `Ver acta` en `/caja/turnos/`, habilitando acceso de lectura del acta al `ADMIN`. |
| **HAL-018** | Media | ✅ Corregido | `identity/services.py`, `identity/tests.py` | `deactivate_employee` bloquea la desactivación de un vendedor que tenga un turno abierto en `CashShift`, exigiendo cerrar el turno primero. |
| **HAL-019** | Media | ✅ Corregido | `inventory/forms.py` | `InitialLoadProductForm` muestra `"Este producto ya tiene una carga inicial registrada o no está disponible."` cuando se intenta recargar un producto. |
| **HAL-020** | Media | ✅ Corregido | `inventory/templates/inventory/stock_overview.html`, `initial_load_form.html` | Botones de acción en `/inventario/stock/` filtrados por rol (`Existencias iniciales` para `ALMACENERO`, `Ajuste físico` para `ADMIN`) y nota aclaratoria en carga inicial. |
| **HAL-021** | Media | ✅ Corregido | `identity/templates/identity/base.html`, `product_list.html`, `supplier_list.html` | Añadidos enlaces de consulta (`Catálogo de productos` y `Proveedores`) al menú del Almacenero y ocultados botones de mutación para roles no-Admin. |
| **HAL-022** | Media | ✅ Corregido | `inventory/forms.py`, `inventory/services.py` | Validación estricta de RUC (`^\d{11}$`) y formato de teléfono en `SupplierForm` y `create_supplier`. |
| **HAL-023** | Media | ✅ Corregido | `catalog/templates/catalog/category_list.html`, `category_form.html` | Añadido aviso explícito sobre la restricción de alcance R1 (solo la categoría «Productos enlatados» está habilitada para registro de productos). |
| **HAL-024** | Media | ✅ Corregido | `catalog/forms.py` | Rechazo de nombres sin caracteres alfanuméricos, nombres duplicados (`name__iexact`) y precios en notación científica (`1e5`). |
| **HAL-025** | Media | ✅ Corregido | `sales/templates/sales/sales_checkout.html` | Script en vivo recalcula Base imponible, IGV, Total a cobrar y Vuelto estimado al escribir descuento o efectivo recibido. |
| **HAL-026** | Media | ✅ Corregido | `identity/forms.py`, `identity/services.py`, `identity/views.py`, `employee_edit.html` | Rechazo de contraseñas débiles/triviales (`12345678`, caracteres repetidos) y nuevo campo opcional `new_password` para restablecer contraseña al editar empleado. |
| **HAL-027** | Media | ✅ Corregido | `identity/views.py`, `identity/tests.py` | Bloqueo temporal en sesión tras 5 intentos fallidos consecutivos de inicio de sesión. |
| **HAL-028** | Media | ✅ Corregido | `identity/views.py`, `identity/templates/identity/login.html`, `identity/tests.py` | Preservación y redirección segura (`url_has_allowed_host_and_scheme`) al parámetro `next` tras iniciar sesión. |
| **HAL-029** | Baja | ✅ Corregido | `identity/templates/identity/base.html`, `templates/403.html`, `stock_overview.html`, `product_movements.html` | Unificada marca `Minimarket · Sistema de gestión` en títulos `<title>`, cabecera pública, pie de página y pantalla `403`. |
| **HAL-030** | Baja | ✅ Corregido | `templates/404.html` | Creada plantilla `404.html` personalizada en español con botón `"Volver al inicio"`. |
| **HAL-031** | Baja | ✅ Documentado | `sales/views.py` | Comportamiento idempotente mantenido por diseño de pruebas de Sprint 1; documentado en trazabilidad. |
| **HAL-032** | Baja | ✅ Corregido | `stock_overview.html`, `adjustment_form.html`, `sales_checkout.html` | Añadidas explicaciones contextuales de *Stock físico vs. Stock vendible*, *Ajuste (+/-)* y recálculo de *IGV / Base imponible*. |
| **HAL-033** | Baja | ✅ Corregido | `sales/views.py`, `sales/urls.py`, `sales_draft.html`, `cash_close.html` | Añadido endpoint `POST /ventas/descartar/` (`sales-draft-discard`), botón `"Descartar venta"` en `/ventas/` y enlace directo desde `/caja/cerrar/`. |


