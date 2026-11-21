# Seguridad: contrato vigente y evidencia · 12/11/2026

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


[Diseño](../../02_Diseno_Tecnico_R1_PMV.md) · [Contratos DOC01-06/DOC02-04](../../auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Verificación](../../auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md) · [Baseline](../../auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/r1-pmv/docs/seguridad.md).

Tres roles comerciales exclusivos. `seed_pmv` contiene tres cuentas activas (una por rol) y una cuarta inactiva de prueba; no existe cuarto rol. Semillas no autorizadas en base operativa. Secretos del ambiente no se inspeccionaron ni modificaron.

Sesión servidor/CSRF/Argon2/permisos existentes tienen pruebas acotadas. Middleware revoca sesión rechazada y04D verifica muestras de reactivación; no protege automáticamente escrituras externas a servicios. Revalidar actor/propiedad dentro de la transacción; denegar sin mutación. ConfiguraciónHTTPS/cookies/perímetro productivos no examinados.

Requisitos pendientes: portal técnico restringido, limitación de tráfico medida, retención explícita, eventos fiables y redacción de exc_info, carrerasintegrales y bloqueo300s antes del piloto. ResetADMIN/desbloqueo explícito auditado; cambio de correo/reactivación no limpia sanción silenciosamente como política nueva. Mensajes uniformes5fallos/15min no sustituyen esas capas. HU-LOG-01/pantalla es futura; logging técnico es actual.

PG17 objetivo;SQLite no demuestra locks. PruebasPG18.4 acotadas no certifican toda seguridad. No rotar secretos, publicar conexiones, modificar.env ni ejecutar semillas por una instrucción histórica. Migración/despliegue requieren autorización separada.
