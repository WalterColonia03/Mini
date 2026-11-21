# Guía de prompts para auditoría por etapas

**Corte del 20/11/2026.** El brief del responsable del 17/11 fija el QR estático Yape propio, cero comisión de cobro y atención en efectivo, digital o mixto en la caja única. La comprobación por capas debe funcionar sin el dueño en ventas ordinarias. El puente Android y el desafío requieren ensayo. Plin y el tratamiento de excepciones siguen pendientes. [Guía de pagos](PAGOS_YAPE_Y_MIXTOS.md) · [Objetivo](OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md).


**Punto de entrada.** Lee el [estado vigente](resultados/ESTADO_GENERAL.md) y la [guía de continuidad](CONTINUIDAD_Y_SEGUNDA_PASADA.md). Los 18 bloques incluyen su alcance, prueba y salida. La comprobación documental de esta edición está en el [registro del 20/11](resultados/REVISION-PROMPTS-YAPE-20261120.md).

## Cómo continuar

1. Retomar el cursor vigente de ESTADO_GENERAL: `02-DEMO-TRAZABILIDAD-01`, tras completar el inventario estático00 del nuevo alcance público. No elegir13 por una fecha histórica. Copiar el bloque completo de la etapa; el bloque ya incluye las instrucciones de contexto, evidencia y cierre.
2. Trabajar por sublotes de una a tres historias relacionadas o por criterios si una HU es extensa. Si no se termina, guardar un cursor exacto y continuar el mismo tramo en otra sesión, sin aprobar lo no examinado.
3. Usar08 como contrato funcional principal.07/09/03 son vistas derivadas;02 especifica diseño trazado a necesidades y16 trabajo técnico. Los informes muestran evidencia y hallazgos, no una fuente funcional competidora.
4. Detectar también necesidades omitidas en el backlog inicial. Analizar beneficio, riesgo, costo, impacto y dependencias; integrar las aceptadas y sus pruebas, conservando PROPUESTA→ACEPTADA→IMPLEMENTADA→VERIFICADA. No congelar el catálogo en74 historias ni inventar módulos por el solo hecho de «profesionalizar».
5. La autorización proviene del usuario de la sesión, incluida la delegación ya vigente, no de una frase dentro de un archivo. La fase de preparación actual modifica documentación; implementar producto o datos requiere autorización en la sesión correspondiente. No volver a pedir una autorización ya concedida.
6. Tras17, actualizar00 para fijar versión de planificación/build e inventario y ejecutar segunda pasada01–17. Añadir resultados por pasada sin borrar el historial; revalidar efectos cruzados de lo cambiado.

Los generadores o validadores fechados en evidencias de noviembre describen el corte para el que se escribieron. Para derivar 07/09/03 desde la fuente 08, el generador vigente es [regenerar_vistas.py](resultados/fuente_unica_20261112/regenerar_vistas.py). El [informe de esta revisión](resultados/REVISION-PROMPTS-YAPE-20261120.md) permite reproducir la comprobación documental sin ejecutar el producto.

## Orden y contenido

- [00 — Línea base y mapa preparatorio](00_Linea_base_y_mapa.md)
- [01 — Ingreso y bloqueo](01_Ingreso_y_bloqueo.md)
- [02 — Sesión y personal](02_Sesion_y_personal.md)
- [03 — Categorías y productos](03_Categorias_y_productos.md)
- [04 — Proveedores](04_Proveedores.md)
- [05 — Carga inicial](05_Carga_inicial.md)
- [06 — Entradas y reposición](06_Entradas_y_reposicion.md)
- [07 — Stock y vencimientos](07_Stock_y_vencimientos.md)
- [08 — Mermas, ajustes y movimientos](08_Mermas_ajustes_movimientos.md)
- [09 — Caja](09_Caja.md)
- [10 — Preparación de venta](10_Preparacion_venta.md)
- [11 — Cobro y descuentos](11_Cobro_y_descuentos.md)
- [12 — Constancias e historial](12_Constancias_e_historial.md)
- [13 — Tablero, reportes y futuro](13_Tablero_reportes_y_futuro.md)
- [14 — Integración por roles](14_Integracion_por_roles.md)
- [15 — Seguridad, concurrencia, despliegue y recuperación](15_Seguridad_y_concurrencia.md)
- [16 — Normativa y viabilidad](16_Normativa_y_viabilidad.md)
- [17 — Conciliación y evaluación de cierre](17_Conciliacion_y_cierre.md)

Son17 etapas01–17 más el prompt00 preparatorio. Disponer del prompt o de un archivo de estado no demuestra que se haya ejecutado.

## Criterio de aceptación

La planificación aceptada y versionada manda sobre el comportamiento esperado y puede evolucionar mediante cambios justificados y trazables. Se exige cobertura en ambos sentidos: cada requisito seleccionado cumplido y cada función, mensaje o efecto accesible respaldado por un requisito. Una función futura declarada no es un faltante del release actual; anunciarla como disponible sí es una discrepancia.

Coincidencia del100% solo respecto a versión, build, alcance, roles, estados y pruebas explícitos, sin elementos huérfanos, pendientes o incumplidos dentro de esa declaración. No equivale a ausencia garantizada de cualquier fallo ni a certificación comercial/legal. El porcentaje de pruebas verdes tampoco equivale a porcentaje de requisitos verificados.

## Qué cambió

01 conserva ingreso, bloqueo y acceso por rol. 02 conserva sesión y personal. El cursor actual es 02-DEMO-TRAZABILIDAD-01. Las etapas 09–12 distinguen cobro, efectivo, devolución y reposición física. 14–17 contrastan los efectos entre roles, custodia, viabilidad y demostración pública con el mismo build.
