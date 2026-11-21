# Etapa 13 · revalidación final de navegador

**13/11/2026, America/Lima · primera pasada · sublote 13-B-final. Resultado: pendientes visuales aplicables resueltos.** Continúa 13-B-01, no reinicia la auditoría. Cubre el panel mínimo y sus consultas; no cierra ventas, caja, catálogo o inventario completos. [Informe de etapa](../ETAPA-13.md) · [evidencia nueva](../evidencias/13-B-final-20261113/) · [validación de evidencia](../evidencias/13-B-final-20261113/validacion-evidencia.json).

## Identificación y conservación

HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, con cambios locales preexistentes conservados. 08 al ejecutar navegador: SHA256 `f4f6f82177685bfd492f5473bed945cd9add67b2a700639f40fe7444d449bc48`. Build local de 183 archivos: `99686b95a2c1d612bd4944a6cc0e7d16ab601c3f73d142e546a5f0c8ca30e215`. [Entrada](../evidencias/13-B-final-20261113/baseline.json) y [reanudación](../evidencias/13-B-final-20261113/resume-20261113T2023.json) coinciden con el manifiesto final 13-B, ruta por ruta. La comparación con 13-A identifica los cambios posteriores y evita reutilizar sus capturas como aceptación visual final.

Windows, Python 3.12.10, Django 5.2.18, servidores HTTP locales de desarrollo y SQLite aislada. Navegador real Chromium integrado en la herramienta CUA; acciones de login, navegación, filtros, borrador y confirmación por interfaz. Ningún cliente Django sustituye este recorrido. Las pruebas PostgreSQL se identifican aparte. Puertos 8135 (primera fixture), 8136/8137/8138 (sesiones independientes de ADMIN/VENDEDOR/ALMACENERO sobre la fixture de integración) y 8139 (vacía), restringidos a 127.0.0.1. Cookies separadas por sesión de prueba, sin modificar autenticación ni permisos del producto. Credenciales ficticias conservadas fuera de capturas, informes y logs.

| Fixture nueva marcada | Uso | Estado al comenzar |
|---|---|---|
| `etapa13-20261113T165829Z-04bf8084` | Revalidación visual V01–V33 | Poblada, sin integración consumida |
| `etapa13-20261113T170135Z-89bd0eff` | Cobro UI I01–I12, fallos F01–F08, interacción N y permisos P | Independiente de probes; 5 ventas de todas las fechas, 3 del día, lote de integración 3 |
| `etapa13-20261113T165832Z-6eed3923` | Vacíos y cuentas E01–E12 | Todas las tablas de negocio vacías; solo cuentas/roles de prueba |

El día de Lima de las tres fixtures es 2026-11-13, calculado al crearlas. La prueba reutilizable obtiene la fecha de `fixture.json`; no impone esa fecha en nuevas ejecuciones. Los registros históricos sintéticos de ayer/mañana prueban fronteras, no cobros históricos reales. No se reutilizó el borrador ficticio de 13-A ni se le atribuye una venta.

Los archivos `.txt` nuevos son snapshots DOM completos, no los diffs AX parciales anteriores. Los `.meta.json` registran hora UTC, URL, pasada y sublote donde se capturaron. Para V01–V33, sin metadato individual, el índice conserva la hora de guardado del filesystem y no la presenta como una medición exacta del instante de observación. [Índice y hashes](../evidencias/13-B-final-20261113/indice.json). Las capturas muestran el producto final; la edición documental posterior de 08 registra este resultado sin cambiar HUs, criterios ni código.

## 13-B-01 · roles, consultas y mensajes

| Evidencia nueva | Resultado observado y esperado |
|---|---|
| V01 login | Describe resumen diario y operaciones por rol, sin prometer reportes futuros. |
| V02 ADMIN, V25 ALMACENERO, V29 VENDEDOR | ADMIN: 3 ventas, S/60.06, S/5.06, 1 turno, 3 críticos, 6 próximos, 5 vencidos. Almacén solo 3/6/5; vendedor sin resumen administrativo. Fecha Lima, ventas/descuentos del día frente a estados actuales y recarga manual explícitos. |
| V03 inventario, V04 catálogo | Igualdad 5/5 incluida en críticos. Producto inactivo conserva 11 físicos/8 vigentes y estado; categoría inactiva 10/4 y estado; ninguno recibe badge Stock bajo. No se ocultan sus vencidos ni sus existencias. |
| V05–V08 vencimientos | 30 días: 11 filas = 5 vencidos + 6 próximos. 1 día: 7 = 5+2; 3650: 13 = 5+8. Vacío retorna 30. Cuenta/lista coherentes, hoy vencido, día 30 incluido, día 31 fuera de la ventana 30. |
| V09–V12 inválidos | 0, 3651, `abc` y 5000 dígitos: mensaje de rango/formato, control vuelve a 30 y conserva 11 filas; sin 500. [Resumen](../evidencias/13-B-final-20261113/vencimientos-resumen.json). |
| V13–V14 historial | Enlace «Historial de ventas (todas las fechas)» abre 5 ventas/S/243.39/S/8.39 de descuento. Al aplicar Fecha exacta del panel: 3/S/60.06/S/5.06. No confundir los conjuntos general y diario. |
| V25 / P04 recepción | «Registra lotes de mercadería recibida para productos que ya tienen carga inicial». Explica recepción, no autorización de compra ni una funcionalidad SOL futura. |

Las tarjetas de los tres roles y sus rótulos se observan en V02/V25/V29. Se conserva el inventario de 45 grupos de Inicio y 12 de destinos; la apertura de las ocho tarjetas ya demostrada en 13-A se hereda solo como navegación a sus rutas. Las plantillas de destino sin cambios conservan esa evidencia, sin dar por auditadas sus operaciones. Los tres enlaces del resumen se siguieron otra vez en este build y sus conjuntos se compararon expresamente.

## 13-B-02 · cobro mediante interfaz y persistencia

| Momento | ADMIN | ALMACENERO | Lote / efecto |
|---|---|---|---|
| I01–I02 inicial | 3 / 60.06 / 5.06 / 1 / 3 / 6 / 5 | 3 / 6 / 5 | 3 unidades |
| I03 borrador 2×S/3.55; I04–I05 recarga | Sin cambio | Sin cambio | 3; no venta confirmada adicional |
| I06 revisión del cobro | Total S/7.10, efectivo S/10.00, vuelto S/2.90 en el formulario | — | Todavía borrador |
| I07 confirmación por VENDEDOR | Constancia V-00000001, total 7.10, recibido 10.00, vuelto 2.90 | — | Una venta nueva |
| I08 panel aún abierto | Conserva los valores anteriores hasta recarga, conforme al mensaje | — | No promete actualización automática |
| I09–I10 recarga | 4 / 67.16 / 5.06 / 1 / 4 / 6 / 5 | 4 / 6 / 5 | 1 unidad; igualdad con mínimo 1 |
| I11 constancia recargada; I12 y Z01 tras reinicio local | Misma venta y cifras posteriores | P04/P07: 4 / 6 / 5 | No duplicado |

Orden de ADMIN: ventas, total, descuentos, turnos abiertos, críticos, próximos, vencidos. [Borrador](../evidencias/13-B-final-20261113/I03-borrador.jpg) · [constancia](../evidencias/13-B-final-20261113/I07-cobro-confirmado.jpg) · [panel posterior](../evidencias/13-B-final-20261113/Z01-panel-final.jpg).

Testigos de solo lectura SQLite: `B02-before.json`, `B02-draft.json`, `B02-after-reload.json`, `B03-final-sin-mutacion.json`. Ventas y lote idénticos antes/después de preparar; tras confirmar existe exactamente una venta adicional, total 7.10 y lote 1. Huella de todas las tablas catalog/inventory/cash/sales idéntica entre el testigo posterior y el final (`39b3f964cdad14874df9aed1fc1a41356d39d25b4cd790c8014bc54e698e5d01`), incluyendo después de errores, recargas y denegaciones. Excluye sesiones/identidad, que cambian legítimamente al autenticar. Los testigos corroboran las acciones del navegador; no las sustituyen. La recarga comprobada no constituye una garantía universal ante cualquier fallo de red o doble envío; la idempotencia de servicios tiene evidencia separada en PostgreSQL.

## 13-B-03 · vacío, fallo, rechazo e interacción

| Evidencia | Resultado |
|---|---|
| E01 | Visitante de Inicio redirigido al ingreso con retorno, sin cifras expuestas. |
| E02–E07 | ADMIN siete ceros; almacén tres ceros; vendedor sin resumen. Inventario sin productos/alertas, vencimientos sin lotes, historial sin ventas. `B03-vacio-final.json` verifica cero filas en todas las tablas de negocio. |
| F01–F08 | Fallo real inyectado al ejecutar un SELECT de negocio en panel, inventario, vencimientos e historial: página 500 autónoma «No se pudo completar la solicitud», sin ceros ni detalles internos; al retirar el fallo vuelve la consulta poblada correcta. |
| V26–V28 / P05–P07 | ALMACENERO denegado en historial global de ventas, turnos y empleados; retorno a su inicio sin exposición. |
| V30–V32 / P02–P03 | VENDEDOR denegado en inventario, vencimientos y catálogo administrativo. Panel propio sigue disponible. |
| E08–E12 | Cuenta desactivada pierde acceso y vuelve al login; tras restaurar puede entrar. Rol de prueba inválido produce 403 sin resumen; restaurado ADMIN al terminar. |
| V15–V22, D11 | Fecha imposible, desde ilegible, hasta fuera del rango representable, rango invertido, vendedor/turno inválidos y carácter nulo: mensajes específicos, sin ventas listadas ni 500. Correlativo de 5000 caracteres: conjunto vacío; limpiar recupera la consulta general. [Resumen D11](../evidencias/13-B-final-20261113/D11-resumen.json). |
| V23–V24, V33, N02/N04/N05 | Ancho real 390 px, panel ADMIN y VENDEDOR legibles, controles de filtros disponibles, etiquetas ajustadas y tablas con desplazamiento interno. |
| `keyboard-panel.json`, N04/N05/N06 teclado | Salto al contenido y Tab hacia enlace de inventario con contorno visible; filtro activado con teclado. Flecha derecha mueve las tablas de inventario, vencimientos e historial manteniendo foco visible; scrollLeft positivo, documento sin desborde horizontal mayor que 390. |

El fallo se inyecta desde soporte aislado `audit13c_faults.py` usando `connection.execute_wrapper`, sobre las cuatro rutas autorizadas y SELECT de negocio; no mediante un endpoint público ni una modificación del producto. Es un fallo de consulta simulado, no un ensayo de caída física del motor o de infraestructura. Sustituye la limitación del arnés anterior que inyectaba fallo de render en tres destinos. [Controles de prueba y restauración](../evidencias/13-B-final-20261113/controls.jsonl). Los POST denegados, métodos no admitidos y variantes adicionales de filtros se conservan de servidor compatible; no se inventa su ejecución por UI.

## Recuperación de herramientas y límites de medición

El bloqueo de navegador del corte anterior quedó superado mediante el navegador integrado autorizado. Después de la pausa de la sesión, las pestañas y servidores locales ya no estaban disponibles. Se reiniciaron los servidores propios, se volvió a comprobar el hash del producto y se creó una nueva pestaña HTTP local. La pestaña inicial con conexión rechazada terminó en una URL de error `data:` no admitida: no se controló ni se sorteó esa restricción. La navegación nueva al servidor disponible funcionó y permitió completar los casos. No se usaron controladores externos ni se sustituyó UI por Client.

Se conservan dos limitaciones del arnés: `N01-historial390` se guardó cuando el override había afectado otra pestaña y su ancho era 1280; **no acredita 390 px**, queda sustituido por `N02-historial390-real` y las mediciones N04–N06. `keyboard-table.json` no demostró desplazamiento con End; la prueba posterior con flechas sí lo demuestra. El primer `B01-after-readonly.json` omitió el lote de integración por comparación UUID con/sin guiones; no implica lote ausente. La normalización del testigo se corrigió antes de B02; ese archivo antiguo se conserva y no se usa para afirmar el cambio 3→1. Una lectura del selector `.table-responsive` en inventario falló porque allí es `.table-wrap`; se corrigió usando la región observada, sin alterar la página.

Los overrides de pantalla se retiraron, la cuenta de la fixture vacía quedó activa con ADMIN y los fallos se desactivaron. Servidores propios detenidos al finalizar. No se modificaron datos operativos ni se desplegó. La muestra no certifica todos los dispositivos, lectores de pantalla o combinaciones de filtros; cubre los casos pendientes comprometidos junto a la cobertura compatible de servidor.

## Cómo repetir el recorrido en otro día de Lima

1. Desde la raíz, usar `r1-pmv/.venv/Scripts/python.exe` y los scripts en `auditoria_por_etapas/resultados/soporte/`. Ejecutar `audit13_run.py new` dos veces para crear las fixtures pobladas de lectura y de cobro. Ejecutar `audit13_run.py new empty` para la vacía. Registrar los tres directorios nuevos y la fecha local de sus respectivos `fixture.json`.
2. Para cada proceso local, fijar `AUDIT13_RUN_DIR` al directorio marcado y `AUDIT13_SESSION_SLOT` a `admin`, `warehouse`, `seller` o `empty`. Ejecutar `audit13c_server.py PUERTO_LIBRE`. Los tres procesos usados para el cobro comparten el directorio nuevo de integración y usan slots distintos. Los puertos concretos de este informe son los de la ejecución registrada.
3. Ingresar por navegador con las cuentas de prueba de cada fixture. Seguir las tablas V, I, E y F en orden. Para la integración, conservar abiertas las sesiones de ADMIN y ALMACENERO mientras VENDEDOR prepara y confirma. Abrir el historial general, introducir en Fecha exacta el día de Lima de la fixture y comparar. Recargar la constancia y los dos paneles.
4. Para F, usar `audit13c_control.py fault RUTA` con el directorio de integración y luego `fault off`. Para E, usar `audit13c_control.py account inactive`, `account restore`, `account invalid-role` y `account restore` con el directorio vacío. Verificar el resultado visible tras cada cambio. Para las tablas estrechas, medir el ancho efectivo de la pestaña, navegar con teclado, comprobar foco/desplazamiento y restaurar el tamaño.
5. Registrar los resultados en una carpeta de evidencia nueva. Los archivos de este corte identifican fecha, build y fixtures históricos. El testigo `audit13c_witness.py` lee la base marcada con `mode=ro`. Sus salidas y las de `audit13c_close.py` están dirigidas al directorio fechado de este informe y usan creación exclusiva. Terminar los servidores propios al concluir.

## Evidencia compatible y cursor

[Servidor 13-B](13-B-servidor.md): 100/100 poblado, 100/100 vacío y 160/160 regresión. [PostgreSQL 13-B](13-B-postgresql.md): 37/37 comprobaciones y 6/6 tests, 5 intercalaciones corregidas, 25 lecturas durante 22 commits independientes, fronteras Lima y precisión; volumen 2008 productos/20014 lotes/30006 ventas. Las suites se solapan. Se verificaron resultados y hashes frente a los 183 archivos vigentes, sin repetirlas indiscriminadamente. No se atribuyen esas ejecuciones a la sesión visual ni se convierte SQLite en evidencia de concurrencia PostgreSQL.

**Cursor terminado:** 13-B-01, 13-B-02, 13-B-03 y disposición final de 13-B-04. Etapa 13 finalizada en primera pasada para el panel mínimo y consultas acotadas. PostgreSQL 17, volumen/SLA productivos, decisiones comerciales de futuros y auditorías completas de otros módulos conservan sus límites; no son funciones entregadas ni defectos actuales relegados. **Siguiente etapa: 14, NO EJECUTADA. Segunda pasada no iniciada.**
