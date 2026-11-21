# Integración PostgreSQL14 · primera pasada · 14/11/2026 Lima

Este artefacto aporta comprobaciones de integración que estaban pendientes en14-I. No declara ejecutada ni completada la etapa15. Se ejecuta un clúster nuevo de **PostgreSQL18.4 x64 Windows**, READ COMMITTED, en loopback y puerto aleatorio, con datos ficticios. El proyecto prevéPG17:18.4 no certifica la versión17 ni un entorno productivo.

## Aislamiento y reproducción

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/ejecutar.py <directorio-de-evidencia-nuevo>
```

El runner no acepta DSN externo. Usa `C:/Program Files/PostgreSQL/18/bin`, crea un directorio temporal con marcador propio y nombre aleatorio, genera credenciales efímeras, configura Django antes de abrir una conexión y comprueba `current_database()` y `data_directory`. El secreto y el archivo de contraseña no se publican. El clúster se detiene al finalizar; su carpeta temporal se conserva para diagnóstico, sin borrar bases ajenas. Los archivos de evidencia contienen huellas de todas las fuentes antes/después, hash08, tiemposUTC, versión y observaciones; cada ejecución exige una carpeta nueva y conserva las fallidas.

## Corridas preservadas

| Corrida | Resultado | Interpretación |
|---|---|---|
| [diagnóstico-1](diagnostico-1/results.json) |0/12; fuentes cambiaron|Coincidió con edición de modelos inventory antes de existir0011; los casos fallaron al crear lafixture por columna adjustment_origin_id ausente. No acredita defecto del build final. Clúster inicializó/migró/detuvo correctamente|
| [diagnóstico-2](diagnostico-2/results.json) |16/16; fuentes estables|Primera ejecución tras0011 y cambios cash/sales. Carreras, colisiones, rollback, lectura concurrente y checks monetarios pasan|
| [diagnóstico-3](diagnostico-3/results.json) |19/19; fuentes estables|Agrega doblePOST desde dos sesiones merma/ajuste y rollback de recepción con reintento. Registro previo conservado; el cierre usa la corrida final siguiente|
| [final, vigente](final/results.json) |**19/19; fuentes estables**|14/11/2026,10:28:21–10:28:35 Lima; clúster detenido. Revalidada sobre build congelado; [compatibilidad por archivo](final/compatibilidad-build.json)|

Las primeras corridas no guardaban hash del propio runner; la variante vigente lo añade para la revalidación final. Los resultados originales no se reescriben para atribuirles una versión posterior.

La corrida final copia el [runner ejecutado](final/runner-ejecutado.py) y [08 ejecutado](final/08-ejecutado.md). Fuente08 SHA256 `32270f6b6f32d8aec7c3f4883f20eef2229e3bb26da8f0c0369fd047e3f8e700`; build canónico de209fuentes `ef8bc3fa42ebf84377ec8b910f38acee1ecc7e12f0c252a59ab72adbcbccdd65`. El manifiesto del navegador usa otro conjunto/serialización: su buildruntime `ec783ac6febb289f70efbda37d7e742ad1305088982ad1e4e6f6694549cdd172` coincide por todos los archivos con el finalPG, sin sustituir una huella por otra. El número exacto de archivos consta en los mapas; hashes distintos por algoritmo/conjunto no se interpretan como deriva.

## Matriz requisito → ejecución nueva

| ID de caso | Requisito / entrada | Esperado y observado |
|---|---|---|
|PG14-01|RN05/C04, CP-HU-INV-02-002. Dos llamadas mismaUUID/actor, merma2 de10|Dos resultados con el mismoUUID de baja; una fila y saldo8. BackendPID distintos y espera de lock observada|
|PG14-02|RN05/C04. Otro actor reutiliza la clave mientras primero confirma|Primero éxito; segundo ValidationError; una baja, saldo8, sin revelar resultado ajeno|
|PG14-03|DOC03AI/C02/C03. Dos recepciones con la mismaUUID/contenido/actor|Una recepciónC5@7 sobre10@3; físico15, promedio4.3333. Dos llamadas recuperan el mismo documento|
|PG14-04|DOC03AI/C03. Dos entregas realesC5@7 con distintaUUID/actor|Dos recepciones y lotes físicos deC, físico20; identidad comercial no se confunde con reintento técnico|
|PG14-05, cuatro variantes|RN05/C04, RN14, venta4 frente a merma3 o ajuste−3 sobre5|Se fuerza cada ganador: venta primero deja1 y una venta, inventario primero deja2 y ninguna venta. Perdedor ValidationError, nunca stock negativo ni escritura parcial|
|PG14-06|RN05/C04. DosADMIN ajustan−4 sobre5|Primero confirma, segundo rechaza, saldo1 y un ajuste|
|PG14-07|CT-ROLLBACK. Error después de guardarLot en merma y ajuste|Todas las tablas de negocio conservan su huella anterior, incluso registros/snapshots/costo. Excepción inyectada no equivale a caída de proceso|
|PG14-08|INV02/CA04, RN05/C04. Ocho conexiones con distintos lotes/actores proponen el mismo correlativoB inicialmente|Ocho confirmaciones, ocho referencias únicas consecutivas. La barrera fuerza la colisión inicial; no es una carrera que casualmente se ejecutó en serie|
|PG14-09|INV04/DEC08. Un ajuste−2 confirma en otra conexión entre lectura de lotes y composición delKardex|HTTP200, muestra saldoNo disponible durante la lectura incoherente; recarga posterior muestra8. No inventa un saldo, no demuestra snapshot transaccional global ni estabilidad entre páginas durante escrituras|
|PG14-10|RN05/C02/C04. Nuevo lote HALLAZGO+2 con mismaUUID concurrente sobre físico5|Un nuevo lote con adjustment_origin, un ajuste y físico7; las dos llamadas recuperan misma operación|
|PG14-11|RN05/C02/C04. DosADMIN, distintasUUID y el mismo nombre comercial nuevo|Un origen confirmado; segundo ValidationError por lote existente, sin duplicar; físico7|
|PG14-12, seis variantes|DEC11/C03 y límites. SQL directo quantity1,000,000, total/efectivo negativos, contado/esperado negativos o diferencia inconsistente|PostgreSQL rechaza por IntegrityError; transacción de cada intento revierte y las huellas completas permanecen iguales. No certifica privilegios/hardening de producción|
|PG14-13|DEC-11-TOPE-EFECTIVO-FORM. Acumulado legítimo sobre límite poroperación y capacidad numeric14,2|Fixture histórica explícita de10,000,000 cierra exacto. Acumulado999,999,999,999.99 cierra exacto. Venta adicional se rechaza antes de mutar. Lafixture alta es preparación técnica, no venta nueva porUI|
|PG14-14, dos variantesHTTP|RN05/C04. Dos sesiones independientes, POSTsimultáneo mismaUUID, merma o ajuste−2|Ambas respuestas302 a la mismaURL; una operación y saldo8. Request concurrente utilizaDjangoClient sinvalidaciónCSRF; Chrome aporta el recorrido con middlewareCSRF separadamente|
|PG14-15|DOC03AI/C04, CT-ROLLBACK. Error después deguardar promedio de recepción|Recepción/clave/contador/lotes/costo revierten completamente; reenvío de la mismaUUID confirma una recepción, físico15|

El testigo de persistencia compara tablas `catalog_*`, `inventory_*`, `sales_*`, `cash_*` completas; excluye secretos y tablas técnicas de sesión/auth/admin. Los positivos revisan cantidades/documentos/orígenes requeridos; cada rechazo o excepción comprobado compara testigos cuando se declara así. No se atribuye igualdad de todas las tablas durante una carrera legítima con operación ganadora.

## Cómo se acredita concurrencia

Cada prueba de dos participantes obtiene dosPID de PostgreSQL y usa una barrera. La primera operación retiene la fila relevante mientras la segunda intenta el mismo lock; se consulta `pg_blocking_pids` y se exige observar al primerPID bloqueando al segundo antes de permitir que continúe. Así la evidencia incluye el solapamiento y no solo una lista de resultados de hilos. Se ejercen locks de cuenta, producto o contador según la operación. El caso de ocho correlativos usa una barrera antes del primerINSERT de cada hilo para producir la misma propuestaB y ejercitar reintentos.

## Límites explícitos

Se agregó después una [comprobación independiente del diagnóstico previo de migraciones](MIGRACIONES.md): **4/4 en SQLite en memoria**, usando MigrationExecutor con esquema histórico. No se suma a los19casosPostgreSQL ni se atribuye a otro motor. Los datos legacy inválidos bloquean cash0004/sales0007 sin mutarse; los válidos aplican sin recortarse.

No ejecuta respaldo/restauración, muerte de proceso, reinicio durante escritura, despliegue, tráficoTLS, duración de sesión, privilegios productivos, rendimientoSLA, migración/regularización de datos reales ni prueba sobrePG17. ElKardex muestra incertidumbre honestamente durante el cambio; una lectura coherente en todas las páginas bajo escrituras sostenidas es requisito técnico de investigación15. El cierre14 puede reutilizar estos casos acotados; no debe convertirlos en19criterios completos ni en aprobación de todas las garantías15.

