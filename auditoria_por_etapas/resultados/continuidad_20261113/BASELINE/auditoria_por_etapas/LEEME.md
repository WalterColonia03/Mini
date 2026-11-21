# Guía de prompts para auditoría por etapas

Este paquete organiza una revisión profunda del minimarket. No es una auditoría ejecutada ni prueba que el sistema y la planificación ya coincidan. Los prompts están adaptados a los archivos, roles y rutas observados el 5 de noviembre de 2026; cada ejecución debe verificar el estado actual.

## Cómo usarlo

1. Abre `00_Linea_base_y_mapa.md` y copia el texto del bloque en un chat de Codex con acceso al proyecto. El prompt indica leer el protocolo común; no necesitas pegarlo cada vez.
2. Continúa con los prompts 01–17, preferentemente uno por sesión o chat para limitar el contexto. Abre el archivo correspondiente y copia su bloque. Conserva la misma carpeta del proyecto: los informes permiten que cada sesión retome el trabajo.
3. Si una etapa es extensa, repite su mismo prompt en otra sesión. El agente debe continuar desde el caso pendiente guardado, no repetir o marcar el resto como aprobado.
4. Consulta `resultados/ESTADO_GENERAL.md` y `resultados/ETAPA-NN.md` a medida que se generen. El estado general y el informe de etapa 00 ya existen; los demás informes se crearán al ejecutar cada etapa. Respeta el cursor y los estados pendientes: un inventario no equivale a una aprobación funcional.
5. Los prompts autorizan investigar y corregir defectos inequívocos, crear o proponer documentación y pruebas justificadas, con datos aislados. Decisiones comerciales o de alcance que no puedan inferirse quedan registradas para resolverlas; el trabajo independiente puede avanzar.

## Orden y contenido

- [00 — Inventario y frontera del producto](00_Linea_base_y_mapa.md)
- [01 — Ingreso, credenciales y protección de acceso](01_Ingreso_y_bloqueo.md)
- [02 — Sesión, cierre y gestión de empleados](02_Sesion_y_personal.md)
- [03 — Catálogo y ciclo de vida del producto](03_Categorias_y_productos.md)
- [04 — Proveedores y relación con inventario](04_Proveedores.md)
- [05 — Carga inicial de existencias y lotes](05_Carga_inicial.md)
- [06 — Entradas posteriores frente a reposición](06_Entradas_y_reposicion.md)
- [07 — Existencias, alertas y vencimientos](07_Stock_y_vencimientos.md)
- [08 — Bajas, ajustes y trazabilidad](08_Mermas_ajustes_movimientos.md)
- [09 — Apertura, cierre y cuadratura](09_Caja.md)
- [10 — Preparación de venta y bloqueo de pantalla](10_Preparacion_venta.md)
- [11 — Cobro en efectivo, exactitud e integridad](11_Cobro_y_descuentos.md)
- [12 — Constancias, historial y consultas](12_Constancias_e_historial.md)
- [13 — Panel, indicadores y reportes planificados](13_Tablero_reportes_y_futuro.md)
- [14 — Recorrido completo entre roles](14_Integracion_por_roles.md)
- [15 — Seguridad, despliegue y confiabilidad](15_Seguridad_y_concurrencia.md)
- [16 — Límites normativos y comerciales](16_Normativa_y_viabilidad.md)
- [17 — Cierre de cobertura y preparación de exposición](17_Conciliacion_y_cierre.md)

## Criterio de cierre

La coincidencia se evalúa contra un alcance explícito, requisito por requisito y también desde cada pantalla hacia la planificación. Una etapa no se cierra con parciales, omisiones de prueba o conflictos sin resolver. El porcentaje de pruebas aprobadas no equivale al porcentaje de requisitos verificados. Seguridad y cumplimiento normativo requieren verificaciones independientes; la constancia interna actual no es un comprobante tributario SUNAT.
