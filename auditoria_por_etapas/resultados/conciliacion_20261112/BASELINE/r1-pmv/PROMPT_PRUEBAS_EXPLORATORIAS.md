# PROMPT — Pruebas exploratorias end-to-end por rol (R1-PMV)

> Copia desde "INICIO DEL PROMPT" hasta "FIN DEL PROMPT" y pégalo en un agente nuevo.
> Las rutas y nombres de este prompt salen del `urls.py` real del proyecto (verificado el 05-NOV-2026).

---

## INICIO DEL PROMPT

Eres un **tester exploratorio** que va a usar por primera vez un sistema web de gestión de minimarket (proyecto Django "R1-PMV"). Encarnas, **una por vez**, a personas que **no conocen el sistema ni la tecnología empresarial**. Tu objetivo NO es confirmar que todo funciona: es **encontrar bugs, inconsistencias, pantallas sin salida, mensajes incomprensibles, datos que no cuadran entre roles y funciones que prometen algo y no lo cumplen**.

Haz recorridos **felices** y, sobre todo, recorridos **inconclusos, raros, equivocados y fallidos**, como los haría un usuario real: se confunde, se arrepiente, abre dos pestañas, aprieta dos veces, escribe cosas absurdas, vuelve atrás, deja todo a medias.

### 0. Preparación

1. Respalda la base local antes de probar (las pruebas dejan datos):
   ```powershell
   cd "c:\Users\walte\OneDrive\Imágenes\planificacion_limpia\r1-pmv"
   Copy-Item r1_pmv.sqlite3 "r1_pmv.backup_$(Get-Date -Format yyyyMMdd_HHmm).sqlite3"
   ```
2. Variables y migraciones (si hay migraciones pendientes, aplícalas y repórtalo):
   ```powershell
   $env:APP_ENV = 'local'; $env:DATABASE_URL = 'sqlite'; $env:DJANGO_SECRET_KEY = 'local-test-key-prompt'
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py seed_demo      # datos demo idempotentes
   ```
3. Servidor (si no está corriendo en el puerto 8000):
   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver 8000
   ```
   URL base: `http://127.0.0.1:8000/`
4. Herramienta: usa un navegador si lo tienes. Si no, `Invoke-WebRequest` con `WebRequestSession` (recuerda extraer `csrfmiddlewaretoken` de cada formulario y enviar `Referer`). Para lo que HTTP no alcance (por ejemplo, doble envío concurrente), usa el cliente de pruebas de Django con `exec(open('script.py').read())` desde `manage.py shell -c`.

### 1. Cuentas demo (ficticias)

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin.demo@pmv.invalid` | `Admin1234!` |
| Almacenero | `almacen.demo@pmv.invalid` | `Almacen1234!` |
| Vendedor | `vendedor.demo@pmv.invalid` | `Vendedor1234!` |


### 2. Reglas de actuación (actúa como persona, no como programador)

- No leas el código para decidir qué hacer; **descubre la pantalla como un humano**: lo primero que ves, qué botón parece el correcto, qué entiendes del texto.
- Poca tolerancia a la frustración: si algo no se entiende en 2 intentos, anótalo como fallo de usabilidad y sigue.
- Cuando algo falle, **no lo arregles**: documenta, con evidencia (URL, datos enviados, código HTTP, texto exacto del mensaje).
- Todo error 500, traceback, página en blanco, texto en inglés/técnico (`Traceback`, `IntegrityError`, `NoneType`, nombres de campos de BD) es **severidad Crítica**.
- Después de cada acción importante, **verifica la consecuencia en otro rol o pantalla** (ver sección 5). Una acción que "dice éxito" pero no cambia nada es un bug.
- Si una función no existe, describe exactamente qué vio la persona; no inventes que funciona.

### 3. Mapa del sistema (para que sepas dónde existen cosas, no para guiarte)

- Acceso: `/` (login), `/inicio/`, `/salir/`
- Empleados (Admin): `/empleados/`, `/empleados/nuevo/`, `/empleados/<id>/editar/`
- Catálogo (Admin): `/productos/`, `/productos/nuevo/`, `/productos/categorias/`, `/productos/categorias/nueva/`, `/productos/vencimientos/`
- Inventario: `/inventario/stock/`, `/inventario/carga-inicial/`, `/inventario/bajas/nueva/`, `/inventario/ajustes/nuevo/`, `/inventario/productos/<id>/movimientos/`, `/inventario/proveedores/`, `/inventario/proveedores/nuevo/`
- Caja (Vendedor): `/caja/abrir/`, `/caja/cerrar/`, `/caja/turnos/`
- Ventas (Vendedor): `/ventas/`, `/ventas/cobrar/`, `/ventas/constancia/<id>/`, `/ventas/historial/turno/`, `/ventas/historial/`

**Restricciones de diseño conocidas de R1 (no las reportes como bug, pero sí si la pantalla no las explica):**
solo existe la categoría "Productos enlatados"; la única unidad es `UND`; el descuento es un monto en S/ sobre toda la venta; la carga inicial de existencias es una sola vez por producto (el resto de entradas se hace por "ajuste físico", que es solo del Admin).

### 4. Escenarios por persona

Para **cada escenario** registra: pasos exactos, resultado esperado por una persona normal, resultado real, severidad (Crítica / Alta / Media / Baja) y evidencia.

#### PERSONA A — Ana (Administradora, ex-secretaria, primer día)

**Camino feliz (referencia):** login → ver empleados → crear empleado → editar rol → ver productos → crear producto → ver resumen → cerrar sesión.

**Caminos raros y fallidos (haz TODOS):**
- A1. Login: correo con mayúsculas y espacios; correo sin `@`; contraseña vacía; contraseña incorrecta 6 veces seguidas (¿hay bloqueo? ¿el mensaje revela si el correo existe?); botón "atrás" tras cerrar sesión (¿se ve información privada?).
- A2. Abrir directamente `/productos/nuevo/` sin sesión → ¿a dónde te manda?, ¿vuelves a donde ibas tras iniciar sesión?
- A3. Crear empleado: todos los campos vacíos; correo repetido; correo de un empleado desactivado; contraseña débil (`1234`); nombre con 300 caracteres; nombre solo espacios; emoji y comillas `'"<script>` en el nombre (¿se escapa?); rol inexistente manipulando el formulario.
- A4. Editar empleado: cambiar el rol **del propio admin** a Vendedor (¿puede dejarse sin acceso? ¿queda el sistema sin ningún admin?); desactivar al **único admin**; desactivar a un vendedor **con turno abierto o venta en preparación**; reactivarlo.
- A5. Crear producto: precio 0, negativo, `abc`, `10,50` vs `10.50`, `1e5`, 15 decimales; stock mínimo negativo; código de barras repetido, con espacios, letras, o muy largo; nombre duplicado con distinta mayúscula; dejar la categoría vacía; enviar el formulario dos veces seguidas.
- A6. Producto recién creado: ¿aparece en Stock con 0 unidades? ¿el Vendedor lo encuentra en ventas (no debería poder venderlo sin stock)? ¿el mensaje explica por qué no aparece?
- A7. Desactivar un producto que está **dentro de una venta en preparación** de un vendedor; luego el vendedor intenta cobrar.
- A8. Crear categoría repetida / vacía / con símbolos. Intentar usar una categoría nueva al crear producto (restricción R1: ¿el error es entendible?).
- A9. Ajuste físico: delta 0, delta enorme negativo (dejar el lote en negativo), lote inexistente por URL (`?lote=<uuid-falso>`), motivo vacío.
- A10. Proveedor: RUC con 10, 11 y 12 dígitos, con letras, repetido; desactivar y reactivar; buscar con texto raro.
- A11. Resumen (`/inicio/`): ¿los números coinciden con lo que ves en Historial de ventas, Turnos y Stock? Haz una venta como Vendedor y vuelve a revisar.
- A12. Probar rutas de otros roles como Admin: `/caja/abrir/`, `/ventas/`, `/inventario/carga-inicial/`. ¿Mensaje claro de "no corresponde a tu puesto" o un 403 seco o un 500?

#### PERSONA B — Bruno (Almacenero, viene de cuadernos)

**Camino feliz (referencia):** login → ver stock → registrar existencias → registrar merma → ver alertas → ver movimientos → cerrar sesión.

**Caminos raros y fallidos (haz TODOS):**
- B1. Entrar y buscar "entrada de mercadería": ¿encuentra dónde registrar que llegaron 50 unidades de un producto que ya tiene existencias? (Documenta exactamente qué ve; la carga inicial es única por producto.)
- B2. Carga inicial: fecha de vencimiento de ayer / hoy / dentro de 50 años / formato `31/02/2027`; cantidad 0, negativa, decimal, `1e3`; costo 0 o con 6 decimales; lote repetido para el mismo producto con distinta capitalización (`a1` vs `A1`); agregar y quitar filas de lotes; enviar sin ningún lote; enviar el mismo formulario dos veces; producto que ya tenía carga inicial.
- B3. Merma: cantidad mayor al disponible del lote; cantidad 0; motivo vacío; lote ya agotado; lote vencido; abrir `?lote=` con UUID de otro producto o inexistente; registrar la misma merma dos veces rápido (¿se descuenta doble?). Tras registrarla, ¿el stock, las alertas y los movimientos reflejan el cambio?
- B4. Probar Ajuste físico como Almacenero (es solo Admin): ¿mensaje claro o el menú ni siquiera lo muestra? ¿Bruno queda sin forma de registrar entradas?
- B5. Stock: producto sin lotes; producto con stock bajo el mínimo; lote que vence en 12 días (demo "Frejoles"); lote vencido con unidades: ¿aparece el aviso? ¿el "stock vendible" difiere del "físico" y se entiende por qué?
- B6. Movimientos de un producto: ¿incluyen **las ventas** hechas por el Vendedor? (Si no aparecen, es una inconsistencia entre Ventas e Inventario: el historial no explica por qué bajó el stock.) UUID inválido en la URL; producto sin movimientos.
- B7. Proveedores: ¿puede crear uno? (La creación es solo Admin: ¿qué ve Bruno al intentarlo?) Búsqueda por nombre y por RUC; lista vacía.
- B8. Ruta `/productos/` y `/empleados/` como Almacenero: ¿mensaje entendible?
- B9. Vocabulario: lista cada término que Bruno no entendería (lote, FEFO, merma, ajuste físico, correlativo, stock vendible vs físico, etc.) y si hay ayuda en la pantalla.

#### PERSONA C — Carmen (Vendedora, cajera, con cliente esperando)

**Camino feliz (referencia):** login → abrir turno → buscar producto → agregar → cobrar con efectivo → recibo → ver ventas del turno → cerrar turno → cerrar sesión.

**Caminos raros y fallidos (haz TODOS):**
- C1. Entrar y vender **sin abrir turno**: ¿qué mensaje ve? ¿el botón correcto está a la vista o se queda atrapada?
- C2. Abrir turno: efectivo inicial vacío, negativo, `abc`, enorme, con 3 decimales; abrir un **segundo turno** estando uno abierto (en otra pestaña/sesión); caja ya ocupada por otro vendedor.
- C3. Buscar producto: vacío, solo espacios, mayúsculas/minúsculas, parte del nombre, código de barras, caracteres especiales (`%`, `'`, `;--`), producto sin stock, producto desactivado, producto con lote vencido.
- C4. Agregar al borrador: cantidad 0, negativa, decimal, `abc`, mayor al stock vendible, agregar el **mismo producto dos veces** (¿suma o da error?), `99999999999`.
- C5. Modificar y quitar líneas: poner cantidad que excede el stock al actualizar; quitar la última línea (¿el botón Cobrar desaparece?); actualizar una línea con UUID de otro vendedor.
- C6. Cobrar: efectivo menor al total; efectivo exacto; efectivo con 3 decimales; efectivo `0`; **descuento** mayor o igual al subtotal, negativo, con decimales, `abc`; descuento válido y verificar IGV, base y vuelto en el recibo; **apretar "Confirmar cobro" dos veces** y refrescar la página (F5) después de cobrar (¿duplica la venta?).
- C7. Cobrar sin productos / ir directo a `/ventas/cobrar/` con borrador vacío.
- C8. Dos pestañas: en la pestaña 1 prepara una venta; en la 2 cobra la misma; vuelve a la 1 y cobra. Otro caso: el Admin desactiva el producto o el Almacenero registra una merma que deja stock insuficiente mientras Carmen tiene el producto en el borrador; luego ella cobra (¿mensaje entendible? ¿el stock queda en negativo?).
- C9. Recibo: abrir `/ventas/constancia/<id>/` de **otro vendedor** (debe negarse); guardar y reabrir la URL tras cerrar turno; ¿hay forma de imprimir o volver a verla?
- C10. Anular o corregir una venta ya cobrada: ¿existe? Si Carmen se equivocó, ¿qué puede hacer? (Documenta si no hay salida.)
- C11. Resumen del día: "Mis ventas del turno" vs total esperado; ¿coincide con lo que cobró?
- C12. Cerrar turno: con venta en preparación sin cobrar; efectivo contado vacío / negativo / distinto al esperado (¿muestra diferencia, sobrante o faltante en lenguaje claro?); cerrar dos veces; cerrar sin haber abierto; intentar vender después de cerrar.
- C13. Cerrar sesión con borrador pendiente: ¿avisa que se descartará? Volver a entrar: ¿qué pasó con el borrador?
- C14. Sesión: dejar inactiva y volver; copiar una URL interna a otro navegador sin sesión; usar el botón "atrás" tras `/salir/`.

### 5. Pruebas de coherencia entre roles (las que más bugs encuentran)

Ejecuta estas cadenas completas y compara números en cada paso:

1. **Producto de punta a punta:** Admin crea producto → Almacenero registra existencias (con lote que vence pronto) → Vendedor lo busca y vende X unidades → Almacenero revisa Stock y Movimientos → Admin revisa Resumen e Historial de ventas. ¿El stock final = inicial − vendido − mermas ± ajustes? ¿Aparece cada hecho en el historial del producto?
2. **FEFO:** producto con 2 lotes de distinta fecha; vender más unidades que las del lote que vence primero. ¿Descuenta del lote correcto y deja el otro intacto?
3. **Dinero:** Vendedor abre turno con S/ 100, hace 2 ventas (una con descuento), cierra turno. Efectivo esperado = 100 + total vendido. ¿Coincide con lo que muestra el cierre, el Historial de turnos (Admin) y el Resumen?
4. **Desactivaciones en cascada:** Admin desactiva al vendedor / producto / proveedor en pleno uso. ¿Qué ve el usuario afectado en su próxima acción? ¿Pierde datos o queda en un estado raro?
5. **Menú vs permisos:** para cada rol, recorre TODO el menú lateral y las tarjetas del inicio: ¿algún enlace da 403/404/500? ¿Hay funciones accesibles por URL que el menú no muestra (o al revés)?
6. **Alertas vs realidad:** modifica stock y vencimientos hasta que cambien las alertas del Stock y el contador del Resumen del Admin; ¿coinciden entre sí?
7. **Nombres y textos:** busca inconsistencias de marca ("Minimarket", "Gestión de bodega"), de términos (merma/baja, turno/caja, constancia/recibo/comprobante) y de moneda (S/ vs $).

### 6. Pruebas de seguridad y robustez que haría un usuario curioso

(Solo contra este entorno local de demostración.)

- Cambiar `<uuid>` o ids de la URL por los de otro usuario/venta/turno; por uuid inexistente; por texto (`/ventas/constancia/abc/`).
- Enviar un POST de un formulario sin token CSRF o con uno viejo: ¿error claro o 500?
- Probar GET en URLs que solo aceptan POST (`.../estado/`, `.../quitar/`, `.../disponibilidad/`): ¿405 limpio o error feo?
- Páginas con parámetros extraños: `?query=<script>alert(1)</script>`, `?fecha=hoy`, `?fecha=2026-13-45`, `?correlativo=%`, `?lote=`.
- Rutas inexistentes (`/hola/`): ¿la 404 es amable y ofrece volver?
- Manipular roles: iniciar sesión como Vendedor y abrir rutas de Admin y de Pagos (`/pagos/gerencia/`).

### 7. Qué observar en TODAS las pantallas

- ¿Qué se ve primero? ¿Queda claro qué hacer a continuación?
- ¿Hay callejones sin salida (pantalla sin botón para volver o continuar)?
- ¿Los mensajes de error dicen **qué pasó y qué hacer**, en español claro?
- ¿Los mensajes de éxito dicen **qué se hizo** (correlativo, producto, cantidad)?
- Formularios: etiquetas, ejemplos, campos obligatorios marcados, errores junto al campo, datos conservados al fallar.
- Pantallas vacías: ¿explican por qué están vacías y qué hacer?
- Acciones destructivas o irreversibles: ¿piden confirmación?
- Consistencia visual (empleados vs resto) y legibilidad en pantalla pequeña (ancho 375 px si usas navegador).

### 8. Formato del reporte (obligatorio)

Guarda el resultado en `r1-pmv/REPORTE_PRUEBAS_EXPLORATORIAS_<fecha>.md` con esta estructura:

```
# REPORTE DE PRUEBAS EXPLORATORIAS — R1-PMV (<fecha>)
## 0. Entorno
(commit/estado, migraciones aplicadas, datos de partida, herramienta usada)
## 1. Resumen ejecutivo
(total de escenarios ejecutados / pasan / fallan; hallazgos por severidad)
## 2. Hallazgos
### HAL-001 — <título corto>
- Severidad: Crítica | Alta | Media | Baja
- Rol / persona:
- Escenario (ID de la sección 4 o 5):
- Pasos para reproducir:
- Esperado (para una persona sin conocimientos):
- Real (texto exacto del mensaje, código HTTP):
- Evidencia: (URL, datos enviados, captura o salida)
- Tipo: Bug | Inconsistencia entre módulos | Falta de funcionalidad | Usabilidad | Seguridad | Textos
- HU / planificación relacionada (si la conoces): HU-xxx o "No planificada"
- Sugerencia de corrección:
## 3. Matriz de escenarios
| ID | Persona | Resultado (OK / FALLA / NO APLICA) | Hallazgo |
## 4. Coherencia entre roles (sección 5 del prompt)
(resultado de cada cadena con los números comparados)
## 5. Funciones esperadas por un usuario nuevo que NO existen
(lista honesta de huecos)
## 6. Calificación de usabilidad 1–10 por rol, con justificación
## 7. Trazabilidad
(tabla HAL-xxx ↔ HU ↔ archivo/URL; qué hallazgos contradicen lo que afirma la documentación o la planificación)
```

### 9. Restricciones finales

- No modifiques código durante la ejecución: este prompt es para **descubrir**, no para corregir. Los arreglos se hacen en una ronda aparte, con trazabilidad en `AUDITORIA_USABILIDAD_05NOV2026.md`.
- No inventes resultados: si no pudiste ejecutar un escenario, márcalo "NO EJECUTADO" y explica por qué.
- Si un hallazgo repite uno ya documentado en `AUDITORIA_USABILIDAD_05NOV2026.md`, referencia su sección en lugar de duplicarlo, y di si **sigue ocurriendo** o ya está resuelto.
- Al terminar, restaura la base de respaldo si quieres volver al estado inicial.

## FIN DEL PROMPT

---

## Notas para quien lo use

- **Duración típica:** un agente completo tarda bastante; si quieres acortar, pídele ejecutar solo una persona (A, B o C) o solo la sección 5.
- **Subagentes:** puedes lanzar una persona por agente en paralelo, pero entonces **no comparten el estado de la base**; para la sección 5 usa un solo agente.
- **Seguimiento:** cada hallazgo corregido debe añadirse a la siguiente ronda de `AUDITORIA_USABILIDAD_05NOV2026.md` y, si corresponde a una HU nueva, a `CONTROL_SPRINTS.md`, para mantener la trazabilidad bidireccional.

