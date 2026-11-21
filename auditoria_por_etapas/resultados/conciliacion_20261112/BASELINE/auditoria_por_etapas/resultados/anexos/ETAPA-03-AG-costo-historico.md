# 03-AG / 06-B · Costo histórico frente a reposición

11/11/2026, America/Lima. Sublote de frontera completado; etapas 03, 06 y 11 no se declaran cerradas. Protocolo leído completo; cambios preexistentes conservados. Repositorio en `r1-pmv`; no se encontraron AGENTS.md dentro del espacio inspeccionado. XLSX ausente, sin lectura ni modificación; su papel histórico permanece en el inventario03. No se usó Jira.

## Inventario y fuentes

Se retoma el inventario completo de [03](ETAPA-03-inventario.md), la conciliación [03-W](ETAPA-03-W-conciliacion.md) y sus actualizaciones Y/Z/AF: nueve HU,27 CA,23 CUMPLE en muestras anteriores y cuatro futuros CAT03/04. Esta sesión no vuelve a aprobarlos. Categorías distintas de enlatados siguen seleccionadas por DOC03-01, con UND y vencimiento obligatorio; editar/eliminar categorías sigue futuro. Lector conserva evidencia y alcance previos. Desactivar fichas no equivale a retiro sanitario.

Fuentes precisas del sublote: HU-INV-01b/CA01–02 (`08:330–336`), RN-14 (`07:181–195`), RN-28 (`07:325–329`), VEN01c/CA06 (`03:121`), VEN02a/CA02 (`08:585–587`), DT-08 y esquema de detalle (`02:39,117,143`), tareas S1-VEN01C-TXDB/AUTO y VEN02A-SVC (`16:153–165`). Backlog09, releases01, planning14, CONTROL_SPRINTS y guía21 conservan su papel de planificación/estado histórico, no evidencia de ejecución. RN-01/DOC-03AB-01 sigue en conflicto frente a entrada directa.

| Elemento / actor | Fuente → código/pantalla → evidencia | Estado y siguiente acción |
|---|---|---|
| INV01b/CA01–02, RN14; ALMACENERO | Dos lotes10×2 y10×4; costo3. Vender2 deja18; ingresar10×6 exige `(18×3+10×6)/28=4.0714`. `register_stock_entry` antes guardaba4.1429 por valorar los lotes remanentes. Chrome/ORM reprodujeron ambos resultados. | INCUMPLE inicial → CUMPLE muestra corregida. No cierre de todo06. |
| RN28, VEN01c/CA06; VENDEDOR | `checkout_sale` → `SaleLine.unit_cost`, copia del producto bloqueado dentro de la transacción. Venta anterior3.0000, siguiente4.0714; las columnas previas permanecen iguales. | CUMPLE muestra nueva. Ventas antiguas carecen del dato; no recuperable automáticamente. |
| VEN02a/CA02, RN26; VENDEDOR | `/ventas/constancia/<uuid>/`: recarga tras entrada conserva todo el texto; no muestra costo. Captura inspeccionada. | CUMPLE en muestra acotada. Historial/impresión completos→12. |
| RN29; ADMIN y VENDEDOR | POST directo `/inventario/entrada/` devuelve403 y no cambia instantánea; ALMACENERO confirma por menú. | CUMPLE muestra. No auditoría integral de permisos. |
| Concurrencia RN14/RN28 | Dos conexiones PostgreSQL y observador: entrada primero→venta4.0000; venta primero→venta3.0000 y promedio posterior4.0714. Stock28 en ambos. | CUMPLE dos órdenes con bloqueo real observado. |
| Migración sales0005 | Nueva columna decimal14,4 nullable; copia SQLite y PostgreSQL preservan columnas antiguas; costos de líneas anteriores quedanNULL. | CUMPLE ensayo; despliegue NO EJECUTADO. |

## Auditoría inversa: acciones, campos, mensajes y salidas

La pantalla de entrada conserva el inventario completo de formularios/límites [03-AB](ETAPA-03-AB-recepcion.md), también registrado en `inventory-before.json` de cada corrida: producto obligatorio existente con carga inicial, proveedor opcional, número de lote normalizado/único por producto, cantidad entera positiva, costo positivo hasta cuatro decimales y vencimiento obligatorio. No se repiten ni se aprueban de nuevo todas sus fronteras. Esta muestra usa lotes A/B/C,10 unidades, costos2/4/6 y fechas futuras60/90 días. Confirmar existencias/Confirmar entrada son acciones expresas; cada una redirige a `/inventario/cargas/<uuid>/`.

Rutas recorridas desde menús: carga inicial, entrada posterior, preparación `/ventas/` (campo búsqueda, cantidad2, Agregar), `/ventas/cobrar/` (efectivo20, Confirmar cobro), constancia y stock. La venta muestra precio9, importe18, base15,25, IGV2,75, efectivo20 y vuelto2. La consulta de stock final muestra26 unidades tras dos ventas de2. La constancia permanece idéntica después de la reposición. El promedio se guarda4.0714 y se muestra4,07 al almacenero. ADMIN participa aquí solo en la prueba de acceso denegado, sin gestión de catálogo nueva.

`unit_cost` es salida interna del servicio, no campo editable ni entrada HTTP: decimal14,4, sin default, `editable=False`, `NULL` reservado al dato histórico desconocido. No se añadió texto ni costo en la constancia del cliente. No se agregó reporte de ganancias. RN28 justifica este campo; no es un extra sin requisito.

## Defectos y correcciones

**H-03AG-01, P1, RN28:** el modelo carecía de costo de venta. Ahora el servicio copia `average_cost` del producto ya bloqueado, junto con el resto del detalle. La migración no rellena históricos con el costo actual ni con cero. La idempotencia devuelve la misma venta sin actualizar su costo. El costo queda protegido de reposiciones normales; no se añadió inmutabilidad SQL general de ventas frente a escrituras externas.

**H-03AG-02, P1, RN14:** la entrada recalculaba desde costos originales de los lotes restantes después de FEFO, contradiciendo el promedio móvil especificado. Ahora usa cantidad vigente anterior×promedio anterior más costo de entradas. Sin stock vigente anterior usa el promedio de la entrada. Conserva exclusión de vencidos, incluida la regresión BUG005. No se cambiaron las reglas de recálculo de merma/ajuste.

**Límite pendiente P1:** la política de valoración cuando conviven vencidos y vigentes, o después de merma/ajuste que recalcula desde lotes, necesita conciliación con RN14. Este corte demuestra el caso con todos los lotes vigentes y el caso de cero stock vigente; no acredita todos los movimientos. No se rebaja la regla ni se oculta la diferencia.

## Pruebas, fallos conservados y reproducción

- Chrome157.0.8103.39 automatizado, SQLite nueva por corrida, tres cuentas ficticias; evidencia antes y después con instantáneas ORM completas del detalle. El primer intento de instrumentación leía una lista reducida de columnas: se corrigió el soporte y se repitió antes de modificar el producto. La ausencia inicial del costo se acredita con la segunda corrida y el esquema, no con esa lista reducida.
- 350/350 métodos finales (`sales inventory catalog cash identity`), `check` y `makemigrations --check --dry-run` correctos. Cuatro métodos nuevos cubren costo anterior/posterior/reintento, desconocidoNULL, stock agotado y rechazo íntegro por lote duplicado.
- PostgreSQL18.4:3/3 casos, dos carreras y migración. El primer ensayo no llegó a ejecutar casos por omitir display_name en las cuentas ficticias; corregido en soporte. La primera regresión tuvo seis fallos: cuatro por esa fixture, uno por nombres de cookies del runner y uno real en la rama de vencidos introducida por el cambio. Se corrigieron y se repitió la suite completa; no se cambiaron expectativas históricas para hacerla pasar.
- Migración en copia SQLite nueva: integridad/FK y contenido comercial anterior conservados; costos antiguosNULL. No se migró el original. PostgreSQL también verificó dos ventas anteriores con todas sus columnas conservadas.
- `git diff --check` global detectó líneas vacías finales preexistentes en catalog/forms.py, identity/app.css e identity/tests.py; no se atribuyen ni corrigen en este corte.

Índice de archivos y resultados concretos: [evidencia consolidada](../evidencias/03-AG-indice.json). Conserva intentos fallidos y resultados anteriores; no sumarlos como nuevas pruebas.

```powershell
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03y_browser_run.py ag-after
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03ag_pg.py
$env:AUDIT03K_DEFAULT_COOKIES='1'
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03k_run.py tests sales inventory catalog cash identity
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03ag_migrations.py
```

`ag-before` es un reproductor para la revisión anterior: sus expectativas de defecto deben fallar con el código corregido. El soporte configura bases marcadas y no carga `.env`; verifica HMAC antes de autenticar. El Python de Microsoft Store no pudo arrancar bajo sandbox y se ejecutó con permiso fuera de él. No hubo acceso a cuentas reales. Servidores detenidos y puertos cerrados; hashes protegidos conservados. Original SHA256 `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`. Datos ficticios finales conservados: tres productos, tres lotes, dos ventas,26 unidades del producto A y turno de pruebaOPEN; no afirmar cierre de caja.

## Propuestas y cursor exacto

**T-03AG-COST01, implementada/verificada:** persistir costo unitario al cobrar, migración sin inferencia histórica y pruebas de reposición/reintento/concurrencia. Respalda tareas TXDB/AUTO existentes, no duplica una HU.

**PROP-03AG-LEGACY01, propuesta para REP07/etapa13:** dado un detalle cuyo costo esNULL, cuando se calcule rentabilidad, entonces identificar costo desconocido y separar cobertura conocida; nunca usar cero o el costo actual silenciosamente. Actor ADMIN; sin nuevas entradas; costo no visible al cliente; depende de RN28 y selección de REP07. Agregar criterio y prueba a backlog/matriz al seleccionar ese reporte; aquí no se implementa ni se aprueba REP07.

**Cursor 03-AH / 06-C / AUD03AH-COSTO-VENCIDOS01:** preparar dos lotes con costos distintos y vencimientos diferentes, vender por FEFO, avanzar fecha de negocio hasta vencer uno y registrar reposición. Contrastar cantidad física/vigente y valoración contra RN14 y BUG005. Después contrastar merma y ajuste con RN14/RN28; conservar ventas ya cobradas y documentar alternativas si la política no es inferible. No repetir el caso todos-vigentes ya aprobado sin nueva brecha.

Despliegue, clasificación de cinco fichas antiguas, recepción multiproducto, respuesta incierta de reposición, caída de servidor, solicitud aprobadaRN01, trazabilidad venta→lote, cuarentena y retiro sanitario siguen pendientes. No se deduce cumplimiento normativo ni finalización de otros módulos.


**Corrección de atribución, 03-AI (11/11/2026).** Los POST403 de este corte no aseguraban token CSRF propio: acreditan rechazo sin escritura, pero por sí solos no prueban autorización por rol. La corrida final03-AI verificó explícitamente cinco combinaciones con CSRF válido y plantilla de permiso. Costos, datos y demás observaciones conservan su evidencia. [Detalle y resultados](ETAPA-03-AI-reposicion-respuesta.md).
