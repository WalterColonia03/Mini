# Servidor 14-G · recepción y procedencia

Primera pasada,13/11/2026 Lima. SQLite aislada en memoria; Python3.12.10/Django5.2.18/SQLite3.49.1. Fuente08 ejecutada SHA256 `8d4a7cbede73eac5b09524363e35d4780dc91d8e25ba6fa8f62de32a66c9984c`. No se abrió ni migró la base operativa. Las pruebas nuevas usan cuentas ficticias, servicios y Django Client; la evidenciaChrome adicional usaHTTP real/CSRF.

## Pruebas focales y regresión

[Diez pruebas14-G](../../../../../r1-pmv/inventory/test_audit14g_receipts.py) verifican:

1. Carga10@3; recepciónC10@6 da20/4.5000; segundaC5@8 da25/5.2000. R-00000001/R-00000002; reintento igual y con espacios/costo equivalentes; cambios de cantidad/lote/proveedor rechazan. Selección de merma/ajuste muestra ambas referencias.
2. Orden de líneas invertido devuelve la misma recepción; otro almacenero con la misma clave rechaza sin mutar.
3. ` ab  12 ` y `AB 12` son iguales; duplicado dentro del formulario rechaza; `AB12` es distinto. Legado `OLD  CODE` se compara sin reescribirlo y una fecha contradictoria rechaza.
4. Confirmación ya existente se recupera tras desactivar producto/categoría/proveedor y avanzar el reloj más allá del vencimiento; clave nueva rechaza. Actor revocado no reenvía.
5. Cantidad0, precisión5, vencimiento hoy, UUID inválido/ausente y fila duplicada no cambian tablas. Corrección con la misma clave confirmaR1. Fecha contradictoria del lote rechaza.
6. Ajuste+4 cambia capacidad, pero constancia conserva10UND. Renombrar producto/código/proveedor/RUC/autor/lote/costo no cambia fotografías. GET de constancia/movimientos deja BD igual.
7. ADMIN/VENDEDOR no registran; ADMIN consulta, VENDEDOR403. Contador99999999 rechaza con mensaje y huella idéntica.
8. Inyección de excepción **después de escritura observada** en contador, cabecera, lote, línea de recepción y costo del producto. Cada variante compara todas las25 tablas de negocio y exige rollback total; control positivo posterior confirmaR1.
9. Venta22 consume10 iniciales+10 deR1+2 deR2. Asignaciones enlazan lotes correctos, stock3 y costo histórico/promedio5.2000.
10. Migracióninventory0007→0008 conserva todas las columnas de filas ficticias iniciales/posteriores, sin crear recepciones o líneas para ellas. Restauración de esquema al terminar. Pruebas previas de inmutabilidad de received_at verifican ORM ySQL tras reconstrucción.

| Corrida preservada | Resultado | Interpretación |
|---|---|---|
| focal-1 |7/9, dos errores de fixture|Nombre de argumento del borrador y estado de modelos históricos incompleto; corregidos|
| focal-2 |9/9 en3.074s|Antes de añadir normalización de espacios y ampliaciones de enlace|
| corrida-1 |572/583,11fallos|UUID/ruta/etiquetas/duplicado antiguos y dos regresiones reales: triggerSQLite y consultas. Fuentes cambiaron durante ejecución|
| corrida-2 |582/583 en69.348s, fuentes estables|Quedaba una etiqueta antigua de entrada en prueba08|
| final |583/583; duración en log, fuentes cambiaron|Normalización se estaba ampliando; no es el corte final acreditado|
| **final2** |**584/584 en80.237s**, fuentes estables|System check sin incidencias y makemigrations --check sin diferencias|

Los conjuntos se solapan. La duración de la corrida intermedia debe leerse en su [log](final/regresion-final.txt); el corte acreditado es [final2/log](final2/regresion-final.txt) y su [manifiesto](final2/regresion-manifiesto.json). Build194 `f6ca27baf3813bf8806d449269623e0e9d293e8000dee4cfd83d45dd038cb11c`.

La regresión obligó a preservar el triggerSQLite al cambiar restricciones deLot. La migración lo retira antes de reconstruir y lo instala después, con operaciones inversas simétricas. La consulta de movimientos se optimizó conPrefetch/select_related; se conservó el umbral de15 consultas de la prueba08. Las adaptaciones de pruebas04/06/08/14E y03AG se justifican por UUID requerida, constancia propia y rechazo por fecha contradictoria. Se preservaron las fuentes previas en [producto-antes.zip](../producto-antes.zip).

## Reproducción y límites

Desde la raíz, usar una carpeta nueva:

```powershell
r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-G-20261113/servidor/regresion.py auditoria_por_etapas/resultados/evidencias/14-G-20261113/servidor/repeticion-nueva
```

El runner estableceAPP_ENV=test y SQLite en memoria antes deDjango.setup, guarda log y huellas antes/después, y comprueba migraciones. La prueba de recuperación usa excepciones de aplicación, no caída de proceso. Bloqueos por fila, carrerasPG, saturación, escritura directa de fotografías y base operativa no quedan acreditados. Las pruebas de carga inicial y merma conservan sus pendientes propios.
