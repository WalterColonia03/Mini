# Disposiciones de valoración14-E · 13/11/2026

Primera pasada, continuación14-D. El encargo de la sesión autoriza correcciones acotadas dentro de la integración; RN-14/28 y DOC-03AH-01 ya aceptados fijan el comportamiento. El mandato «CONTINUA» mantiene el trabajo, sin aceptar por sí solo nuevas reglas comerciales. El protocolo aporta procedimiento, no una autorización independiente. No se intervino una base operativa.

| ID | Estado y fundamento | Resolución y evidencia | Límite |
|---|---|---|---|
| D14E-01 | ACEPTADA previamente RN-14/DOC-03AH; IMPLEMENTADA y VERIFICADA en muestra | Recepción usa todas las unidades físicas. F-COSTO18@3,8vencidas+10vigentes, entrada10@6: antes4.5000, después4.0714 | No sanea promedios de historias antiguas ni prueba carrerasPG |
| D14E-02 | ACEPTADA previamente DOC-03AH/C-02, RN-28; IMPLEMENTADA y VERIFICADA | Venta, merma y ajuste negativo no reponderan por compras restantes. Al agotar físico, promedio0. Snapshots conservan costo previo | Asignación a lote y consulta histórica completa siguen pendientes |
| D14E-03 | Concreción técnica ACEPTADA por corrección autorizada contra DOC-03AH/RN-28; IMPLEMENTADA y VERIFICADA | Dos campos Decimal(14,4) nullable en baja/ajuste. Migración0007 sin default/backfill, costo anterior capturado bajo lock antes de salida | NULL de legado no equivale a costo0. editable=False evita formulario, no demuestra inmutabilidad por SQL ni protección de portal técnico |
| D14E-04 | ACEPTADA previamente DOC-03AH/C-03; IMPLEMENTADA y VERIFICADA la rama de rechazo | Ajuste positivo con físico0 rechaza antes de escribir. Mensaje pide investigar y documentar el origen | Captura de costo fiable/fuente conQ0 y lote nuevo sigue pendiente de INV-03. No se prescribe simular una compra |
| D14E-05 | Tarea de verificación necesaria por cambio semántico ya aceptado; VERIFICADA | Se conservan pruebas/fuentes anteriores y se sustituyen las expectativas de excluir vencidos/reponderar/retener costo al agotarse. Se agregan seis tests significativos de fórmula, HTTP, permisos, rollback, legado y migración | Suite verde no demuestra cierre completo de HU ni entorno productivo |
| D14E-06 | PROPUESTA técnica de diagnóstico y recomendaciones14-F, sin intervención operativa | Consultas read-only sobre clon explícito, clasificación de costos desconocidos y alternativas de corte de valoración | No ejecutadas sobre datos reales; una apertura requiere hechos y sustento del negocio. No se inventa el valor |

[Inventario y recomendaciones con beneficio/riesgo/costo/impacto](14-E-inventario.md) · [Antes/después servidor y trazabilidad de tests](../evidencias/14-E-20261113/servidor/INFORME.md) · [Navegador](../evidencias/14-E-20261113/navegador/RESUMEN.md).

## Cambios y cobertura entre módulos

- inventory/services.py: Q físico de recepción; snapshot previo de baja/ajuste; helper de promedio vacío; rechazoQ0. Conserva permisos y transacciones.
- inventory/models.py y migrations/0007_output_unit_cost.py: campos históricos nullable. La prueba migra filas ficticias de0006a0007, compara todos los valores anteriores y exigeNULL nuevo.
- sales/services.py: resetea promedio después de FEFO y de capturar SaleLine. Efectivo, precio y total permanecen sujetos a los contratos de venta y caja.
- Pruebas inventory/tests.py, test_audit06_stock_entry.py, test_audit08_writeoffs_adjustments_movements.py y test_audit14e_valuation.py: las expectativas nuevas provienen de08, con copia anterior preservada.
- 08 conserva criterios y añade representación/estado de ejecución parcial.07/09/03 se regeneran desde esa fuente.02/14/16/21 y continuidad registran alcance real.

## Pendientes y alternativas

Los módulos futuros no pasan a seleccionados y no se crea una HU duplicada por cada campo técnico. La necesidad de auditoría histórica ya existe en DEC-11-MODELO, DOC-03AI y DEC-08-KARDEX. El diseño proporcional propuesto usa asignaciones durables nuevas y preserva ausencias históricas como desconocidas; su implementación concreta se seleccionará en14-F. Reaplicar FEFO a ventas pasadas sería una inferencia insegura.

El costo operativo antiguo puede proceder del algoritmo defectuoso. Alternativas: investigar historia verificable y preparar una apertura sustentada, o mantener cobertura histórica desconocida hasta obtener hechos suficientes. Costo relativo medio, beneficio de valoración trazable, riesgo de falsificar rentabilidad si se rellenan valores por conveniencia. No hace falta esa decisión para verificar el algoritmo con datos ficticios nuevos.

Las garantías de concurrencia y recuperación real conservan etapa15; SQLite y una excepción controlada no sustituyen conexiones PostgreSQL ni caída de proceso. El backlog de NFR ya contiene esos encargos. La constancia de merma dedicada, recepción propia, saldo real/filtros/paginación y ajuste sobre lote nuevo siguen abiertos.
