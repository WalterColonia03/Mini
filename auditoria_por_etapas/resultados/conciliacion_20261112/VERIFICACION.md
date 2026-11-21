# Verificación del código integrado · 12/11/2026

## Suite completa aislada

Ejecución válida:21:48:45–21:49:50UTC (16:48:45–16:49:50Lima). Python3.12.10, Django5.2.18, SQLite nuevo. **434 descubiertos,434 ejecutados, cero fallos, cero errores y cero omitidos**. `check` y `makemigrations --check --dry-run` aprobados. Estos comandos no prueban configuración productiva ni despliegan migraciones.

Evidencia: [summary.json](VERIFICACION/integrated-20261112T214843Z-4c3c50/summary.json), [suite.log](VERIFICACION/integrated-20261112T214843Z-4c3c50/suite.log), [check](VERIFICACION/integrated-20261112T214843Z-4c3c50/check.log), [dry-run](VERIFICACION/integrated-20261112T214843Z-4c3c50/makemigrations.log), [manifiesto antes](VERIFICACION/integrated-20261112T214843Z-4c3c50/protected-before.json) y [después](VERIFICACION/integrated-20261112T214843Z-4c3c50/protected-after.json).

503 archivos protegidos sin cambios durante la ejecución. Base operativa sin lectura de sus tablas y con SHA256 antes/después `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`. El runner bloquea lectura de `.env`, escritura fuera de su directorio propio y conexiones SQLite fuera del entorno aislado; la denegación registrada de lectura `.env` es la comprobación intencional de esa guarda.

Reproducción desde raíz, con dependencias del entorno del proyecto:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION/verify_integrated.py'
```

El runner crea directorio único, cambia cwd a `r1-pmv`, invoca el runner Django completo sin etiquetas/exclusiones y conserva salida. [Código del soporte](VERIFICACION/verify_integrated.py). El primer intento falló antes de ejecutar tests por descubrimiento desde cwd incorrecto; quedó preservado en [resumen del intento](VERIFICACION/integrated-20261112T214801Z-aca835/summary.json) y [fatal.log](VERIFICACION/integrated-20261112T214801Z-aca835/fatal.log). Se corrigió únicamente el soporte nuevo. Ese error no se atribuye al producto.

## Subconjunto PostgreSQL18.4

Nueva ejecución22:42UTC, clúster efímero propio en localhost, datos ficticios y settings que impiden cargar `.env`. [Reporte](VERIFICACION/pg12/evidencias/12-pg-20261112T224240242212Z-9964ca71/pg-report.json). Se verificaron entradas NUL de filtros, frontera diaria de Lima, consultas constantes4→4 y7→7 tras15 ventas adicionales y reintento concurrente de cobro. Dos workers/conexiones terminaron con302 a la misma constancia; una venta para la clave. Puerto60168 cerrado al terminar; archivos protegidos del soporte conservados.

Se copió el soporte12 a [audit12_pg.py](VERIFICACION/audit12_pg.py), sin editar el original ni producto; [preparador y cambios de aislamiento](VERIFICACION/preparar_pg.py). Se añadió exigencia de que terminen ambos workers y haya dos resultados (evita un `all([])` vacuamente verdadero). Se conserva el clúster propio detenido, no se borró recursivamente ninguna carpeta. Claves generadas solo para entorno ficticio; no deben publicarse sus archivos de configuración.

**Límite importante:** son peticiones despachadas con `django.test.Client` en dos hilos contra PostgreSQL real. No son sockets HTTP ni navegador. La barrera permite concurrencia de envío; no demuestra por sí sola cada espera específica en un lock. La prueba no cubre PG17, caída posterior a escritura, todas las carreras ni los contratos nuevos aún sin implementar.

## Rectificaciones de interpretación

- ETAPA09 sí fue ejecutada. Su JSON Chrome tiene68 elementos:67 funcionales más `cero_page_errors`; no70. Informe/estado histórico se conservan y reciben adenda vigente.
- 04-D tiene artefactos y pruebas de revocación posterior al cursor04-C. La muestra raw incluye petición intermedia; servicio desactivar/reactivar cubre ausencia de petición intermedia. No se garantiza bypassraw sin servicio/petición.
- El fallo de queries de producto no guardado se corrigió en05-L; la suite actual incluye ese módulo y03AJ/04D/08/12 sin exclusiones. Los resultados previos con exclusiones no son un fallo actual por sí solos.
- 05-L Chrome/PG y la corrección posterior de guarda no corresponden todos a idéntico build. No se suman como si fuesen una única ejecución. Interrumpir HTTP en espera anterior a escritura no cubre caída después de escritura/COMMIT/motor.
- Historial12: repetir98/98 después del fallo por empate de apertura no corrige la falta de orden total. HU-VEN-05b/CA02 pide filtros y CA03 abre detalle; no hay exigencia de expandir líneas en la lista.

## Qué falta

No se ejecutó navegador nuevo en este corte; las muestras Chrome/lector permanecen en sus informes. PG17, CI/despliegue real, backup/restauración, nuevo E2E integral, volumen/NFR, impresión/dispositivos reales completos y revisión independiente no están certificados. No se probó software que implemente los contratos nuevos de ENCARGOS porque esta fase no autoriza esos cambios. La auditoría no se cierra.

## Reproducción dirigida de los contratos críticos

Ejecución del12/11 a22:19 Lima (13/11 03:19UTC), SQLite nuevo, servicios y ORM reales con fixtures ficticios. [Reporte](VERIFICACION/contrastes-20261113T031920Z-fead5b/report.json) · [Soporte reproducible](VERIFICACION/verificar_contrastes.py). Sin navegador/concurrencia. Guardas impidieron abrir la base operativa o leer.env; hashes protegidos sin cambios.

| Paso | Resultado comprobado actual | Requisito adoptado |
|---|---|---|
| CargarA10×2+B10×4 y vender2 deA | Físico18, promedio3.0000, venta guarda costo3.0000 | Coherente para esta secuencia |
| Avanzar reloj ficticio a vencimiento deA | Físico18, vendible10, promedio3.0000 | Expiración sola no revalúa |
| RecibirC10×6 | Físico28, vendible20, promedio4.5000 | DOC03AH exige4.0714 sobre físico registrado |
| Dar de baja1 vencida deA | Físico27, vendible20, promedio5.0000; venta sigue3.0000 | Salida debe conservar promedio vigente, sin reponderar compras restantes |
| Repetir entradaC | Rechaza lote repetido, sin mutación; devuelve la carga inicial al confirmar primera entrada | Recepción propia/idempotente debe devolver misma recepción ante repetición válida; ingreso real nuevo usa identidad distinta |
| Robo de1unidad ya vencida | Rechaza imponiendo Vencimiento; sin mutación | RN05 permite Robo/faltante con explicación, cualquiera sea vencimiento |
| Baja conADMIN | Permitida y autorADMIN registrado | Se conserva permiso útilADMIN/ALMACENERO en matriz y contrato; solo ajuste queda exclusivoADMIN |
| Persistencia venta | No hay tabla de asignaciones; camposSale no contienen snapshotsvendedor/caja | RN25/26 requieren garantías históricas, aún pendientes |

La reproducción prueba comportamientos actuales, incluidos los que difieren del requisito nuevo. No se modificó el algoritmo ni se hicieron pasar esos comportamientos por cumplimiento de los contratos revisados.
