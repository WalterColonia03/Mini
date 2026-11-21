# Primer intento concurrente en SQLite

Nota de auditoría levantada a partir de la salida de consola del 10/11/2026. Dos conexiones llegaron a la escritura durante la prueba de confirmaciones. La implementación inicial separaba la lectura de la versión de la actualización bajo select_for_update. SQLite informó OperationalError (database is locked) y la vista devolvió un error interno. El proceso terminó sin result.json. Se conservó el directorio de datos de este intento. Solo se acredita el fallo observado, sin atribuir un resultado individual a los otros escenarios.

El cambio posterior compara la versión en el propio UPDATE y la incrementa en esa escritura. [Repetición en SQLite](../03-J-sqlite-race-20261110T172006895618Z/result.json).
