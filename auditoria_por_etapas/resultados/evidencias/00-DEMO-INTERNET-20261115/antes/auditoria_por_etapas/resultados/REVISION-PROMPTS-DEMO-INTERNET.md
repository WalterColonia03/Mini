# Revisión de prompts y objetivo de entrega · 15/11/2026

**Resultado:** actualización documental e inspección del producto; no ejecución de etapas 00–17, no despliegue y no pruebas de pago reales. Se revisaron y actualizaron los 18 prompts copiables, protocolo, continuidad y guía. Se incorporó el objetivo público y se preservó la evidencia local anterior. [Objetivo](../OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md) · [Matriz de pagos y fuentes](../PAGOS_YAPE_Y_MIXTOS.md).

## Decisiones y autoridad

El usuario cambió la entrega de local a internet y pidió QR/Yape, pagos mixtos, cancelaciones, distinción de medios y situaciones difíciles del minimarket. Después precisó que los empleados pueden actuar maliciosamente, la atención debe ser rápida, el dueño no estará siempre presente y no deben hacerse nuevos yapeos para devolver dinero. Optó por transferencias reales pequeñas para la demostración. Estas instrucciones respaldan los objetivos y el refinamiento, no una afiliación, gasto ni una prueba monetaria automática.

Se descartó la propuesta de aprobación obligatoria del dueño en cada cobro. El usuario no eligió todavía un medio concreto de reintegro ni aceptó el costo de Yape Empresa; su demanda de autonomía no equivale a autorizar una salida automática de efectivo. La alternativa Ayudantes está documentada con fuente oficial, costo y límites, sin declararla contratada ni API integrada.

## Problemas prevenidos en los prompts

| Problema encontrado | Corrección aplicada |
|---|---|
| LEEME seguía ordenando iniciar 13 por estado del 13/11 | Leer cursor vigente; nuevo sublote 00 para cambio de objetivo y después 02 |
| ESTADO_GENERAL y continuidad conservaban otros cursores con apariencia de vigencia | Etiquetar secuencias como históricas y declarar que manda el cursor DEMO-INTERNET, conservando resultados anteriores |
| Contexto exclusivamente local chocaba con exposición por internet | Objetivo común y contrato de entrega pública;01-K sigue siendo local, sin reescribir sus resultados |
| Muestras podían leerse como aprobación global | Congelar CA/CP antes de probar; separar sublote, etapa, entorno público y entrega; no recortar denominador tras fallo |
| Pruebas con tiempos de creación implícitos fallaban por empates | Exigir fixtures deterministas y pruebas explícitas de empate/concurrencia; conservar las corridas fallidas |
| El código existente podía terminar aceptado por documentarlo | Fundamento de aceptación y decisión antes de cambios; funciones extras no se aprueban automáticamente |
| Equivalencia de significado podía confundirse con coincidencia literal exigida por el profesor | Exigir redacción exacta y formato de variables en08 o catálogo aceptado enlazado por CA/CP; registrar una brecha si falta antes de implementar o aprobar la interfaz |
| Yape escrito como futuro podía confundirse con funcionalidad lista | HU-VEN-07 seleccionada por nuevo encargo, implementación pendiente; nuevo HU-VEN-10 para mixtos |
| QR/checkbox/código podía confundirse con confirmación bancaria | Fuente receptora legítima; separar comprobación humana/API; código de 3 dígitos no es identificador global |
| Cancelar venta podía interpretarse como dinero devuelto | Separar intento, abono, aplicación yreintegro; prohibir nuevos yapeos y dejar política delegada explícitamente pendiente |
| Solo se miraban permisos visibles | Pruebas servidor/servicio, POST alterado, QR ajeno, pagos de otro cliente, revocación y recuperación |
| Solicitar un reintegro se confundía con autorizarlo o entregarlo | Distinguir permisos de solicitud, autorización, ejecución y configuración del receptor; no imponer aprobación del dueño ni denegación de toda solicitud |
| Rapidez se podía prometer sin medir | Medir captura, pasos, p50/p95 del sistema y espera externa por separado; no omitir controles |
| Una norma de seguridad ajena podía convertirse en obligación del proyecto | En16 delimitar el caso tributario de comprobantes y condiciones del medio de pago, con fuentes y aplicabilidad; no reintroducir retención legal retirada |

## Planificación y producto observados

08 conserva los IDs anteriores y agrega HU-VEN-10: «Cobrar una venta combinando efectivo y Yape». HU-VEN-08/09 eran ideas históricas excluidas y no se reutilizaron; la validación detectó la colisión inicial antes de escribir 08. Se refina HU-VEN-07 y RN-02 con la amenaza interna y el origen de la comprobación. Se añade CT-ENTREGA-ACADEMICA con 6 criterios y 6 CP diseñados. Las fichas de anulación 06a/b/c mantienen su historia y señalan el refinamiento pendiente para la nueva entrega; no se las presenta como implementadas.

Catálogo después:75 HU,35 seleccionadas y40 futuras,301 criterios y121 CP escritos. Antes:74 HU,33 seleccionadas,41 futuras,287 criterios y113 CP. Los recuentos son de planificación, no ejecución.07/09/03 e índice se regeneran desde 08.01/02/14/16/21 y guías se sincronizan; no se compromete un Sprint ficticio ni se aprueban todos los reportes/facturación por añadir pagos.

Inspección: `r1-pmv/sales/models.py` representa efectivo recibido/vuelto; `checkout_sale` valida efectivo y `sales_receipt.html` muestra «Efectivo». `sales/urls.py` no publica endpoints Yape/reembolso/anulación. `qr-minimarket/` contiene una imagen JPG sin prueba de titularidad o vinculación. Por tanto **Yape, mixtos y reintegros no están demostrados ni implementados por esta revisión**. No se modificó producto, base principal ni QR; no se ejecutaron cobros ni movimientos de dinero.

## Recomendaciones, costo y límites

| Recomendación | Beneficio | Riesgo / costo / estado |
|---|---|---|
| Fuente receptora de consulta delegada | Evita que el dueño apruebe cada venta; no da claves de fondos al cajero | Ayudantes Yape tiene comisión y requisitos; no confirma automáticamente al sistema ni impide toda mentira interna. PROPUESTA A EVALUAR |
| Registro separado de abono/aplicación/reintegro | Conserva dinero ante fallo y evita doble aplicación | Diseño/migración de costo medio/alto; referencia real y política pendientes antes de cerrar esquema |
| Reintegros delegados bajo política explícita | Reduce dependencia del dueño sin regalar poder de retirar | No hay medio/topes/permisos aceptados aún; no inventarlos. DECISIÓN PENDIENTE |
| Publicación con URL del proveedor y BD durable | Profesor accede desde fuera y datos sobreviven reinicios | Proveedor/cuotas/costo por verificar; sin contratación automática. PENDIENTE |
| Instrumentación de tiempos separada del banco | Encuentra causas de colas sin debilitar comprobaciones | Objetivo numérico provisional necesita medición pública y carga definida. PENDIENTE |

La consulta oficial de Ayudantes es una alternativa más adecuada que acceso bancario pleno del cajero. No resuelve por sí sola confirmación automática contra un trabajador malicioso: exige aceptar explícitamente el control humano y su conciliación, o conseguir un canal verificado de integración. No se encontró ni probó una solución gratuita que satisfaga simultáneamente todas las restricciones. No se presume que la falta de RUC excluya todas las alternativas: la fuente oficial contempla DNI para Yape Empresa; disponibilidad concreta aún por comprobar.

## Validación de este corte

[VALIDACION.json](evidencias/DEMO-INTERNET-20261115/VALIDACION.json) comprueba presencia de 18 prompts/lecturas comunes, integridad de IDs históricos, ausencia de colisiones, cobertura de criterios porCP, consistencia del generador, enlaces locales nuevos y conservación de producto/BD. [Fuentes antes](evidencias/DEMO-INTERNET-20261115/fuentes-antes.json) y carpeta `antes/` conservan los documentos reemplazados. [Cambios](evidencias/DEMO-INTERNET-20261115/CAMBIOS.json) registra huellas.

Esta validación documental no ejecuta pruebas funcionales de pagos ni certifica cada regla. No se ejecuta otra regresión del producto porque no se cambió código ejecutable ni configuración; los tres fallos externos 01-K siguen registrados para 09/10/12/14. Los estados de otras etapas no se promueven a aprobados.

Se exige además que los literales consten exactamente en08 o en un catálogo aceptado referido por sus CA/CP; equivalencia aproximada o inventario del código no bastan. Los futuros mensajes de pagos requieren ese refinamiento antes de implementar UI. Una ejecución del validador terminó con `UnicodeEncodeError` al imprimir la flecha del cursor en consola Windows CP1252, después de escribir sus JSON; se corrigió solo la serialización de consola a ASCII escapado y la nueva ejecución terminó con código0. Este incidente del soporte no se presenta como fallo funcional ni se oculta como una ejecución exitosa.

Incidencia de la verificación final: una ejecución terminó con código1 al imprimir el carácter de flecha del cursor en una consola Windows con codificación cp1252, después de escribir el JSON. Se corrigió únicamente la serialización de la salida de consola del validador y se volvió a ejecutar con código0. También se sustituyeron dos indicadores constantes de conservación por sus resultados calculados. Esto no fue una prueba ni un defecto del sistema de ventas.

**Cursor exacto:** `00-DEMO-INTERNET-BASELINE-01` → línea base del nuevo objetivo; después `02-DEMO-TRAZABILIDAD-01`. Decisiones paralelas `PAY-CANAL-01` y `PAY-REINTEGRO-01`; no bloquear tareas independientes ni habilitar fondos reales mientras dependencias imprescindibles sigan sin resolver.
