# Unificación de planificación y auditoría de promesas visibles

Fecha de corte:12/11/2026, America/Lima. Solicitud expresa: planificación como fuente principal y única; fichas con épica, código/título, MoSCoW, Fibonacci, descripción, criterios, casos escritos, datos y resultados esperados. Las imágenes aportadas orientan el formato; sus ejemplos de eventos y de errores de usuario/contraseña no se importan como requisitos del minimarket.

## Cobertura y autoridad

La revisión anterior inventarió13 informes originales ETAPA-00..12, sus80 anexos pertinentes (59 Markdown), protocolo, planificación y código/evidencia pertinente. ETAPA-17 registra conciliación parcial;13–16 carecen de informe principal completo localizado. [Inventario y mapa](../conciliacion_20261112/CONSOLIDACION.md), [IDs históricos](../conciliacion_20261112/INDICE_IDS.md) y [verificación con límites](../conciliacion_20261112/VERIFICACION.md) conservan esa trazabilidad.

En este corte se consolidan5 épicas,74 HU,219 CA base,60 criterios de encargos y4J de categorías. Se añaden4 criterios transversales CT-COHERENCIA-UI y110 casos escritos:87 en las fichas,19 de contratos/categorías y4 de superficie visible. Cada caso tiene precondiciones, datos, pasos y resultado esperado. Una prueba puede cubrir varios criterios relacionados; no se confunde cantidad de criterios con número de ejecuciones.

La fuente única es [08](../../../08_Historias_de_Usuario.md).07/09/03 y el índiceJSON se generan leyendo08 y contienen su huella.01/02/14/16/20/21, protocolo y estado de auditoría remiten a ella. Los resultados anteriores quedan como evidencia fechada, no como otra especificación vigente. No se localizó PLANIFICACION_SCRUM_R1PMV.xlsx: su mención en el protocolo no prueba que exista ni permite inventar su contenido.

## Cambios semánticos y registro de decisiones

| ID conservado o nuevo | Decisión/justificación | Estado | Alcance y excepciones | Dependencias y documentos | Criterios verificables |
|---|---|---|---|---|---|
| DEC-FUENTE-UNICA-20261112 |08 reúne contrato funcional y fichas; vistas se derivan para evitar desfases | ACEPTADA por instrucción expresa; IMPLEMENTADA documentalmente; verificación estructural en VALIDACION.json | No autoriza código/DB/despliegue ni cierre histórico |08,07,09,03,00,protocolo y controles | Una definición por ID; campos completos; vistas reproducibles y huellas iguales |
| CT-COHERENCIA-UI | Auditar cada promesa visible y su efecto real, también en sentido interfaz→requisito | ACEPTADA por instrucción expresa; especificada; recorrido integral NO EJECUTADO | Toda ruta/rol/estado; extra sin requisito se registra, no se aprueba automáticamente | Todas las HU seleccionadas, protocolo, matriz | C-01..04 y CP-VISIBLE-001..004 |
| HU-PROV-04/CA-01..02 | Vigencia determina recepción directa actual; SOL permanece futuro | ACEPTADA por delegación; documento actualizado; producto no revalidado por esta edición | Preservar recepción histórica; no convertir proveedor rechazado en omisión | RN01,29, DOC03AB/AI, DEC04RUC | Proveedor desactivado entre GET/POST rechaza sin stock; reactivar habilita nuevas selecciones |
| HU-CAJA-06/CA-01..02 | Aprobación futura agrega revisión sin reabrir/recalcular el cierre | Refinamiento documental futuro; W | Conserva cierre irreversible, contado y diferencia original | RN10,23 y casos de caja | Revisión con autor/observación; acta original idéntica |
| HU-CAJA-07/CA-02 | Un cierre forzado futuro sin arqueo no inventa contado ni cuadre | Refinamiento documental futuro; W | Política de borradores/carreras aún requiere refinamiento | RN23; CAJA01/02 | Sin recuento: No declarado, nunca contado=esperado artificial |
| HU-VEN-02a/CA-03 | Constancia no afirma entrega fiscal externa no comprobada | ACEPTADA por delegación; documento actualizado | Canal real por confirmar antes del piloto | RN26; etapa16 | Leyenda interna visible en pantalla/impresión; ninguna falsa promesa fiscal |
| HU-REP-07/CA-01..03; RN28 | Margen histórico exige costo conocido y base comparable; no promete rentabilidad neta | Refinamiento documental futuro; W; investigación de base del costo | No asumir tratamiento fiscal ni costoNULL=0 | RN14/27/28, datos reales y etapa13/16 | Caso sintético11.80/neto10/costo6 comparable→4/40%; base desconocida→No calculable |
| HU-VEN-06c/CA-01; RN09 | Devolución íntegra vencida no vuelve vendible; recuperar lote original probado | Refinamiento documental futuro; W | Evidencia y destino de vencidos deben refinarse al seleccionar | Asignaciones de lotes y anulaciones futuras | Solo íntegra vigente vuelve vendible a lote original; sin inferenciaFEFO histórica |
| HU-DASH-01/CA-03 | Precisar períodos en Lima hasta el instante de consulta; no mezclar una ventana futura con el día de negocio | Refinamiento documental futuro; W | Latencia máxima de la promesa de actualización todavía requiere refinamiento | DASH01 y su caso escrito | Hoy/inicio de lunes/inicio de mes hasta el corte visible; fechas posteriores excluidas |
| PROP-03C-LIMITES/NOMBRE | Ratificación se fecha12/11 por delegación; no se atribuye aceptación al «continúa» del10/11 | ACEPTADA por delegación; procedencia corregida | No cambia el requisito de nombre normalizado/mínimo | RN06, PROD02/04 | Mínimo10;0..999999; nombre único normalizado global con acentos conservados |

MoSCoW respecto a R1:26M,6S,1C y41W. Las prioridadesS/C no permiten entregar una promesa defectuosa. Las estimaciones orientativas de8 HU aumentan al reconocer contratos antes omitidos: INV01b8, INV038, INV048, VEN01c13, USR038, VEN01a8, VEN02a5 y VEN05b5. Total catálogo268SP; seleccionadas146SP; futuras122SP. Los231SP anteriores quedan históricos. No son estimaciones del equipo, horas trabajadas ni compromiso de Sprint; requieren refinamiento por quienes implementen.

## Verificación y límites

La validación revisa identidad/cobertura de219+60+4+4 criterios,74 fichas y110 casos, MoSCoW/Fibonacci, enlaces/anclas locales, conservación de snapshots, reproducción exacta de vistas y huellas de código/base frente al corte previo. La salida reproducible está en [VALIDACION.json](VALIDACION.json). Esto no acredita por sí solo calidad semántica ni ejecución funcional: se revisaron además cálculo de stock/costo/caja/IGV, permisos, origen histórico, estados futuros y las contradicciones de la tabla anterior.

No se ejecutan los110 casos contra software en esta edición documental. Se conserva434/434SQLite y muestraPG18.4 del corte previo con su build y límites; las pruebas dirigidas previas ya demostraron diferencias de promedio, recepción propia, merma y modelo de ventas. No se vuelve a ejecutar una suite sin cambios de producto para aparentar verificación de requisitos nuevos.

Siguen abiertos: implementación de los contratos, recorrido inverso completo de interfaz/mensajes, PG17 y caída posterior a escritura, restauración/CI/despliegue, datos legacy, parámetros de tráfico/retención, canal fiscal real y base comparable de costo para reporte futuro. No hay fundamento para afirmar coherencia del100% del software ni auditoría cerrada.

## Orden de continuidad

1. Diagnóstico de legado y contratos de costo/recepción/asignaciones de venta; no inventar historia.
2. Implementación autorizada de integridad, idempotencia, permisos, dinero y bloqueo de puesto, con pruebas de rechazo/carreras.
3. Concordancia de mensajes, navegación, cantidades, consultas e impresión con las fichas y CT-COHERENCIA-UI.
4. Recorrido integrado por roles, recuperación, entorno objetivo y evidencia antes del piloto.

Los archivos escenarios.py, suplementarios.py y construir_fuente.py son material del proceso de importación archivado. No son una segunda fuente vigente; el importador rechaza sobrescribir08 una vez publicado. Para cambios posteriores editar08 y usar únicamente regenerar_vistas.py/validar_fuente.py.
