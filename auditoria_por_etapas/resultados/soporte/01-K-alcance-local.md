# 01-K · Alcance de la demostración académica local

**Decisión del responsable del proyecto · 15/11/2026.** Este es un proyecto universitario que se expondrá en vivo con un proyector. El profesor representará a un dueño de bodega/minimarket y evaluará el sistema como un prospecto exigente. La demostración se ejecutará localmente, o en un entorno gratuito de demostración si posteriormente se elige esa opción.

## Problema de negocio y resultado esperado

**AS-IS:** el minimarket registra sus operaciones con cuaderno y lápiz. El crecimiento del negocio hace necesario mejorar el control y la consulta de sus operaciones.

**TO-BE:** utilizar el sistema de ventas y gestión para disponer de información ordenada y trazable, ejecutar las operaciones autorizadas de cada puesto y facilitar el control del negocio. La recuperación de la inversión es una motivación del cliente representado; no se presenta como un resultado económico medido ni garantizado por esta auditoría.

## Regla de evaluación y rectificación de 01-J

Cada pantalla, botón, campo, validación, mensaje y salida que aparezca durante la demostración debe tener respaldo identificable en una HU, su criterio de aceptación y su caso de prueba. Los mensajes exigidos literalmente deben coincidir palabra por palabra. La presencia de una función en el código, en una prueba técnica o en una propuesta redactada por el auditor no constituye aceptación del responsable.

El responsable revoca los agregados de 01-J ajenos a las historias del tramo: límites de tráfico por IP/proxy, mensajes asociados a esos límites y comandos de diagnóstico de identidad. Su retirada debe comprobarse en el producto y en la planificación vigente, regenerando las vistas derivadas desde `08`. Las pruebas históricas de esos extras no son pruebas de aceptación de la demostración.

No se requiere contratar infraestructura ni formalizar responsabilidades de una instalación comercial para cerrar este alcance. Las condiciones de publicación real introducidas en 01-J dejan de ser pendientes de la evaluación local. Esto es una corrección explícita del contexto y del alcance, no una declaración de que una instalación pública haya sido probada.

## Separación entre etapas 01 y 02

| Etapa | Alcance que debe comprobarse | Lo que no se declara cerrado aquí |
|---|---|---|
| **01 · Ingreso y bloqueo** | HU-AUTH-01/02 y RN-17: ingreso de cuentas de los tres roles, credenciales y estados de cuenta, mensajes, bloqueo al quinto fallo por quince minutos, tiempo restante, otro contexto, expiración, sesión y destinos autorizados. La autorización de entrada se contrasta con las opciones de cada rol. | El funcionamiento completo de las operaciones de los módulos de destino. |
| **02 · Sesión y personal** | HU-AUTH-03/04a/04b/05, HU-USR-01..06 y HU-LOG-01 según su selección vigente: salida, gestión de empleados, cambios de rol/estado y efectos sobre sesiones. Las historias futuras conservan esa clasificación hasta una decisión expresa. | No se obtiene su aprobación por ejecutar correctamente el login ni por mostrar los nombres de los roles. |

La correspondencia se basa en [el encargo de etapa 01](../../01_Ingreso_y_bloqueo.md) y [el encargo de etapa 02](../../02_Sesion_y_personal.md). Si se utiliza la expresión general «Ingreso y Gestión de Usuarios/Roles» durante la exposición, debe mostrarse esta división para evitar atribuir a la etapa 01 pruebas de personal que pertenecen a la siguiente etapa.

## Caso del profesor para ventas e historial

El profesor plantea que un cliente compra **100 gaseosas Inca Kola de 3 litros**, solicita una **factura a nombre de su empresa**, pierde el documento y vuelve **dos meses después** para solicitar una copia o su información tributaria.

El responsable pide tratar en el módulo de **Ventas/Facturación e Historial** la conservación y consulta de los comprobantes emitidos por **RUC, número o fecha**, sin permitir su borrado, y la entrega de una copia cuando se solicite. Esta necesidad debe contrastarse con las HU/CA/CP vigentes de ese módulo, precisando la diferencia entre una constancia interna y un comprobante fiscal. Si la planificación vigente todavía no contempla el caso, deberá conciliarse allí antes de declararlo implementado.

Este documento registra el escenario solicitado y su módulo responsable. **No fija un plazo legal, no cita una norma tributaria aún no verificada y no afirma que el sistema ya emita facturas fiscales ni que este recorrido esté implementado o probado.** La verificación normativa y funcional correspondiente se realizará en ventas e historial; no se incorpora como condición de aceptación del ingreso.

## Criterio de cierre académico de etapa 01

La etapa 01 podrá marcarse **cerrada y aprobada para demostración local** cuando la evidencia del build evaluado confirme conjuntamente:

1. Todas las HU y criterios seleccionados del tramo tienen casos ejecutados y resultados correctos en el entorno local con datos aislados.
2. El inventario de elementos visibles y validaciones está vinculado a HU/CA/CP; los textos observados coinciden con la especificación y no quedan extras accesibles sin respaldo.
3. Se comprueban los tres roles, los rechazos pertinentes y sus efectos de servidor/persistencia; la apariencia por sí sola no acredita el resultado.
4. Las discrepancias encontradas se resuelven dentro de la autorización vigente y se revalidan. Las funciones futuras o de otra etapa están identificadas y no se anuncian como disponibles.
5. `08`, sus vistas derivadas, el informe y el estado general describen el mismo alcance y resultado. Las pruebas heredadas se distinguen de las nuevas y no se cuentan ejecuciones inexistentes.

El porcentaje de cierre se refiere únicamente a este alcance académico expresamente definido. La solicitud de mostrar «100 %» no sustituye la comprobación de estos puntos ni autoriza a presentar como aprobada una prueba pendiente. El siguiente paso tras un cierre sustentado es la etapa 02.
