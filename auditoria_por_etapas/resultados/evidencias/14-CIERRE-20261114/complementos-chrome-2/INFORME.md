# Estados complementarios CI14-08/09 · primera pasada de etapa 14

Ejecutado el 14/11/2026, 10:30:31–10:30:39 America/Lima, con Chrome real 157.0.8103.78, Playwright 1.65.1, Django 5.2.18 y SQLite 3.49.1. Base temporal nueva con datos ficticios; no se abrió la base operativa. Este corte revalida los casos de la tabla, no hereda su aprobación de etapas anteriores.

- Build inicial/final estable: `ec783ac6febb289f70efbda37d7e742ad1305088982ad1e4e6f6694549cdd172`.
- Versión de 08 observada al iniciar: SHA256 `32270f6b6f32d8aec7c3f4883f20eef2229e3bb26da8f0c0369fd047e3f8e700`.
- Resultado: 15 observaciones aprobadas; manifiesto en [ejecucion.json](ejecucion.json), resumen en [resultado.json](resultado.json), respuestas de red en [http.json](http.json).
- Cursor local: C09 terminado. El cierre integrado y el estado de la etapa corresponden a ETAPA-14 y ESTADO_GENERAL; este informe no los sustituye.

| Caso | Acción en navegador y criterio | Evidencia y resultado |
|---|---|---|
| C01 | ALMACENERO abre selector de merma sin lotes | Mensaje «No hay lotes con existencias disponibles.»; testigo completo sin mutación |
| C02 | ADMIN abre selector de ajuste sin lotes/productos con carga | Tabla vacía explícita y selector de nuevo lote con una opción inicial; sin mutación |
| C03 × 4 | Merma y ajuste con clave oculta ausente o inválida | Se fuerza el valor del campo oculto mediante DOM y se envía el formulario normal. El servidor devuelve errores; stock, operaciones, ventas y caja permanecen idénticos |
| C04 | ALMACENERO registra merma de 2 sobre lote legado de 10 sin fotografía de entrada | Nueva constancia B, stock 8, promedio ficticio controlado 3, salida 3.0000; muestra «Origen no disponible (registro anterior o incompleto)». Solo cambian Lot y StockWriteOff |
| C05 | Recarga de la constancia anterior | Conserva origen desconocido, cantidad/costo y testigo sin otra baja |
| C06 + recarga | ADMIN consulta Kardex del lote legado | «Sin fotografía de entrada», saldo de cierre «No disponible»; no infiere historia ni modifica datos |
| C07 + recarga | ADMIN consulta Kardex con cabecera inicial incompleta | «La cabecera de una carga está incompleta.», saldo «No disponible»; no modifica datos |
| C08 + recarga | ADMIN consulta lote con dos orígenes técnicos deliberados | «Un lote tiene más de un origen registrado.», saldo «No disponible»; no modifica datos |
| C09 | VENDEDOR intenta acceder directamente a la constancia de C04 | HTTP 403, página de denegación y testigo completo idéntico |

Cada JSON Cxx contiene ruta, rol, texto visible, controles y hashes por tabla. Las capturas corresponden al mismo punto de control. Se inspeccionaron visualmente el selector, el error del ajuste, la constancia con origen ausente y el Kardex de doble origen: textos legibles, ausencia explícita y sin solapamientos visibles en el viewport ensayado. No se deduce accesibilidad global ni cobertura de todos los tamaños de pantalla.

Los estados legado/cabecera incompleta/doble origen se preparan mediante ORM controlado después de comprobar los selectores vacíos, como precisa [fixture.json](fixture.json). No se presentan como operaciones realizadas desde UI ni como migración de datos reales. La costura legado recibe promedio 3 como dato ficticio explícito; no se reconstruye su historia. El corte anterior [complementos-chrome-1](../complementos-chrome-1/ejecucion.json) queda conservado: también pasó las 15 comprobaciones de origen, pero su maestro legado conservaba el valor por defecto 0. Ese corte no acredita tratamiento de valoración incompleta ni saneamiento operativo. La segunda ejecución aísla la ausencia de origen de esa inconsistencia de costo.

La etiqueta técnica «Idempotency key» que aparece al manipular el campo oculto se conserva en la captura de error. La prueba demuestra el rechazo y la ausencia de mutación; no presenta ese campo oculto como un dato que deba escribir el operador. Su redacción fue comunicada al responsable del cierre, sin modificar el producto congelado.

Reproducción desde la raíz del workspace, con Playwright disponible en el directorio temporal de dependencias usado por 14-D:

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/recorrido_estados_complementarios.py auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/complementos-chrome-reproduccion
```

Debe elegirse una carpeta de salida nueva para conservar la evidencia. El runner reutiliza el arnés 14-D y crea/elimina su base temporal en cada ejecución. La fuente exacta del complemento está archivada como [runner-source.py.txt](runner-source.py.txt); SHA256 `8d55b3cf330c20454e20056c701a7f38263df194682b9cad23b66f503e004435`. El manifiesto distingue ese hash del arnés 14-D. La fuente del corte 1 también se preserva en su carpeta, con su hash original verificado.
